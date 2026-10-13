"""
AI Intraday Trading Agent — Autonomous Paper Trading Session Runner (patched)
File: backend/run_session.py

Changes vs. previous version:
  1. Fresh Angel One TOTP login at session start (no more stale .env JWT).
  2. Feed health pre-check: if the first quote cycle returns < 50% LIVE symbols the
     session ABORTS with a Telegram alert and exit code 2. No "0 trades" report is
     written for a session that never received data.
  3. All symbols fetched in one FULL-mode request per cycle (respects Angel's 1 req/s).
  4. Ticks carry per-tick volume deltas and real bid/ask; tick.close = ltp so the
     validator doesn't reject gap-down days (Angel's "close" is the previous close).
  5. Historical 5m candles are preloaded so EMA/MACD/RVOL are valid from 09:25.
  6. Indicator diagnostics are logged at every 5m close, with the failing condition,
     so you can see exactly why the strategy is or isn't firing.
  7. Yahoo fallback is opt-in (--allow-delayed-fallback). Delayed data is not "LIVE".

PAPER TRADING SIMULATION ONLY — Real-money order execution is permanently disabled.
"""

import os
import sys
import argparse
import asyncio
import datetime
from typing import List, Optional, Dict
import pytz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.config import settings
from app.core.logging import logger
from app.core.database import Base, engine, SessionLocal
from app.models.models import PaperPosition
from app.data.adapters.angelone_adapter import AngelOneSmartApiAdapter, ANGEL_NSE_TOKENS
from app.data.adapters.angelone_auth import AngelOneAuth, AngelOneAuthError
from app.data.live_market_provider import LiveNSEMarketDataProvider
from app.paper_trading.engine import PaperTradingEngine
from app.risk.manager import RiskManager
from app.live.streamer import live_streamer
from app.live.data_types import LiveTick
from app.live.indicators import LiveIndicatorCalculator
from app.phase9.session_engine import phase9_session_engine
from app.phase9.execution_realism import Phase9ExecutionEngine
from app.phase9.reporting import Phase9ReportGenerator

IST = pytz.timezone("Asia/Kolkata")
PROVIDER_LABEL = "ANGEL_ONE_SMARTAPI"
MIN_LIVE_FRACTION = 0.5          # abort if fewer than this share of symbols are LIVE at start
MAX_SILENT_SECONDS = 120         # abort if no LIVE quote for any symbol for this long mid-session
HISTORY_DAYS = 4                 # calendar days of 5m bars to preload (covers ~2-3 trading days)


def get_default_watchlist(count: int = 10) -> List[str]:
    drivers = ["RELIANCE", "HDFCBANK", "TCS", "INFY", "TATAMOTORS",
               "ICICIBANK", "SBIN", "BHARTIARTL", "LT", "BAJFINANCE",
               "TITAN", "SUNPHARMA", "MARUTI"]
    return drivers[:count]


async def telegram_alert(text: str) -> None:
    try:
        from app.notifications.telegram_bot import telegram_notifier
        await telegram_notifier.send_message(text)
    except Exception as exc:
        logger.warning(f"Telegram alert failed: {exc}")


def _fmt_ist(dt: datetime.datetime) -> str:
    return dt.strftime("%H:%M:%S")


# ----------------------------------------------------------------------------- diagnostics

def log_5m_diagnostics(symbol: str) -> None:
    """
    Print indicator values and which VWAP_EMA_MOMENTUM condition fails at each 5m close.
    Mirrors the thresholds in app/live/signal_engine.py.
    """
    candles = live_streamer.candle_builder.get_candles(symbol, "5m", limit=100)
    if len(candles) < 5:
        logger.info(f"[DIAG {symbol}] only {len(candles)} x 5m bars; waiting for warm-up")
        return
    ind = LiveIndicatorCalculator.calculate_indicators(candles)
    c = candles[-1]
    long_fail, short_fail = [], []

    if not c.close > ind["vwap"]: long_fail.append("close<=VWAP")
    if not ind["ema_fast"] > ind["ema_slow"]: long_fail.append("EMA9<=EMA21")
    if not 45.0 <= ind["rsi"] <= 75.0: long_fail.append(f"RSI {ind['rsi']} out of 45-75")
    if not ind["macd_hist"] > 0: long_fail.append("MACDh<=0")
    if not ind["rvol"] >= 1.15: long_fail.append(f"RVOL {ind['rvol']}<1.15")

    if not c.close < ind["vwap"]: short_fail.append("close>=VWAP")
    if not ind["ema_fast"] < ind["ema_slow"]: short_fail.append("EMA9>=EMA21")
    if not 25.0 <= ind["rsi"] <= 55.0: short_fail.append(f"RSI {ind['rsi']} out of 25-55")
    if not ind["macd_hist"] < 0: short_fail.append("MACDh>=0")
    if not ind["rvol"] >= 1.15: short_fail.append(f"RVOL {ind['rvol']}<1.15")

    logger.info(
        f"[DIAG {symbol} {c.timestamp.strftime('%H:%M')}] bars={len(candles)} close={c.close:.2f} "
        f"vol={c.volume} vwap={ind['vwap']} ema9={ind['ema_fast']} ema21={ind['ema_slow']} "
        f"rsi={ind['rsi']} macdh={ind['macd_hist']} atr={ind['atr']} rvol={ind['rvol']} | "
        f"LONG {'OK' if not long_fail else 'blocked: ' + ', '.join(long_fail)} | "
        f"SHORT {'OK' if not short_fail else 'blocked: ' + ', '.join(short_fail)}"
    )


# ----------------------------------------------------------------------------- warm-up

async def preload_history(adapter: AngelOneSmartApiAdapter, watchlist: List[str]) -> None:
    now_ist = datetime.datetime.now(tz=IST)
    from_dt = now_ist - datetime.timedelta(days=HISTORY_DAYS)
    # Only bars strictly before the current 5m bucket, so live bars never collide.
    to_dt = now_ist.replace(second=0, microsecond=0) - datetime.timedelta(minutes=1)
    total = 0
    for sym in watchlist:
        bars = await adapter.get_historical_candles(sym, "5m", from_dt=from_dt, to_dt=to_dt)
        added = live_streamer.candle_builder.seed_candles(sym, "5m", bars) if bars else 0
        total += added
        logger.info(f"Warm-up {sym}: {added} x 5m bars seeded")
        await asyncio.sleep(0.4)  # historical endpoint ~3 req/s
    if total == 0:
        logger.warning("Warm-up returned no history; indicators will be unreliable for the first ~2 hours.")


# ----------------------------------------------------------------------------- tick builder

def build_tick(sym: str, d: Dict, source: str) -> Optional[LiveTick]:
    ltp = float(d.get("ltp", 0.0))
    if ltp <= 0:
        return None
    hi = float(d.get("high", ltp) or ltp)
    lo = float(d.get("low", ltp) or ltp)
    op = float(d.get("open", ltp) or ltp)
    # Keep OHLC internally consistent for the validator.
    hi = max(hi, ltp, op)
    lo = min(lo, ltp, op)
    return LiveTick(
        symbol=sym, ltp=ltp, open=op, high=hi, low=lo,
        close=ltp,                                    # NOT the previous close
        volume=int(d.get("volume", 0) or 0),          # per-tick delta from adapter
        bid=float(d.get("bid", round(ltp * 0.9998, 2))),
        ask=float(d.get("ask", round(ltp * 1.0002, 2))),
        spread=float(d.get("spread", 0.0)),
        timestamp=datetime.datetime.now(),
        data_source=source, is_live=True,
    )


# ----------------------------------------------------------------------------- main

async def run_paper_session(
    target_date: Optional[str] = None,
    start_now: bool = False,
    duration_minutes: Optional[float] = None,
    symbols: Optional[List[str]] = None,
    poll_interval_sec: float = 2.0,
    allow_delayed_fallback: bool = False,
    skip_history: bool = False,
) -> int:
    print("=" * 70)
    print("🚀 AI INTRADAY TRADING AGENT (INDIA) — PAPER SESSION RUNNER")
    print("   Mandatory Safety: PAPER TRADING ONLY | Real Orders: DISABLED")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)

    now_ist = datetime.datetime.now(tz=IST)
    date_str = target_date or now_ist.strftime("%Y-%m-%d")
    watchlist = symbols or get_default_watchlist(10)

    unknown = [s for s in watchlist if s not in ANGEL_NSE_TOKENS]
    if unknown:
        logger.error(f"Symbols without Angel One token mapping will be skipped: {unknown}")
        watchlist = [s for s in watchlist if s in ANGEL_NSE_TOKENS]
    if not watchlist:
        logger.error("Watchlist empty after token filtering. Aborting.")
        return 2

    market_open_ist = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    square_off_ist = now_ist.replace(hour=15, minute=15, second=0, microsecond=0)
    target_end_ist = (now_ist + datetime.timedelta(minutes=duration_minutes)) if duration_minutes else square_off_ist

    # ---- 1. Login FIRST, before waiting for the open, so a bad login fails at 09:00 not 09:15
    auth = AngelOneAuth()
    try:
        tokens = auth.login()
    except AngelOneAuthError as exc:
        msg = f"❌ Session {date_str} ABORTED — Angel One login failed: {exc}"
        logger.error(msg)
        await telegram_alert(msg)
        return 2
    adapter = AngelOneSmartApiAdapter(jwt_token=tokens.jwt_token, feed_token=tokens.feed_token)

    # ---- 2. Wait for open if needed
    if not start_now and now_ist < market_open_ist and duration_minutes is None:
        wait_s = (market_open_ist - now_ist).total_seconds()
        logger.info(f"{_fmt_ist(now_ist)} IST: waiting {wait_s/60:.1f} min for 09:15 open...")
        while datetime.datetime.now(tz=IST) < market_open_ist:
            await asyncio.sleep(1.0)

    now_ist = datetime.datetime.now(tz=IST)
    if not start_now and duration_minutes is None and now_ist >= square_off_ist:
        logger.warning("After 15:15 IST square-off; refreshing cumulative report only.")
        res = Phase9ReportGenerator.generate_cumulative_report()
        print(f"✅ Cumulative Pilot Report updated: {res['json_path']}")
        return 0

    # ---- 3. Feed health pre-check (fail closed, fail loud)
    first = await adapter.get_quotes(watchlist)
    live_syms = [s for s, r in first.items() if r.status == "LIVE"]
    frac = len(live_syms) / max(1, len(watchlist))
    for s, r in first.items():
        if r.status != "LIVE":
            logger.error(f"Pre-check {s}: {r.status} — {r.error}")
    if frac < MIN_LIVE_FRACTION:
        msg = (f"❌ Session {date_str} ABORTED — feed pre-check failed: "
               f"{len(live_syms)}/{len(watchlist)} symbols LIVE. "
               f"First error: {next((r.error for r in first.values() if r.status != 'LIVE'), 'n/a')}")
        logger.error(msg)
        await telegram_alert(msg)
        return 2
    logger.info(f"Feed pre-check OK: {len(live_syms)}/{len(watchlist)} symbols LIVE via Angel One.")

    # ---- 4. Session + streamer
    session = phase9_session_engine.start_session(trading_date=date_str, provider=PROVIDER_LABEL, symbols=watchlist)
    session_id = session["session_id"]
    logger.info(f"Started Phase 9 Session {session_id} for {date_str}.")

    live_nse_fallback = LiveNSEMarketDataProvider() if allow_delayed_fallback else None
    paper_engine = PaperTradingEngine(RiskManager())
    live_streamer.connect(PROVIDER_LABEL, is_mock=False, has_credentials=True)
    live_streamer.set_auto_approve(True, expiry_iso=target_end_ist.isoformat())

    if not skip_history:
        await preload_history(adapter, watchlist)

    await telegram_alert(f"✅ Paper session {session_id} started. {len(live_syms)}/{len(watchlist)} symbols live. "
                         f"Ends {_fmt_ist(target_end_ist)} IST. PAPER ONLY.")

    # ---- 5. Main loop
    poll_interval_sec = max(1.5, poll_interval_sec)   # Angel quote endpoint: 1 req/s
    iteration = 0
    valid_ticks = 0
    last_live_quote_at = datetime.datetime.now(tz=IST)
    last_err_log: Dict[str, datetime.datetime] = {}

    try:
        while True:
            cur = datetime.datetime.now(tz=IST)
            if cur >= target_end_ist:
                logger.info(f"Session end reached at {_fmt_ist(cur)} IST. Squaring off.")
                break
            iteration += 1

            quotes = await adapter.get_quotes(watchlist)
            any_live = False

            for sym in watchlist:
                qr = quotes.get(sym)
                source = "ANGEL_ONE_SMARTAPI"

                if (not qr or qr.status != "LIVE") and live_nse_fallback is not None:
                    try:
                        qr = await live_nse_fallback.get_quote_data(sym)
                        source = "YAHOO_DELAYED"
                    except Exception as exc:
                        logger.error(f"Fallback quote error {sym}: {exc}")

                if not qr or qr.status != "LIVE" or not qr.data:
                    # Log errors at ERROR level, but at most once per symbol per minute.
                    prev = last_err_log.get(sym)
                    if prev is None or (cur - prev).total_seconds() > 60:
                        logger.error(f"Quote {sym}: {getattr(qr, 'status', 'NONE')} — {getattr(qr, 'error', 'no response')}")
                        last_err_log[sym] = cur
                    continue

                any_live = True
                tick = build_tick(sym, qr.data, source)
                if tick is None:
                    continue

                res = live_streamer.ingest_tick(tick)
                is_valid = not res.get("tick_rejected", False)
                phase9_session_engine.record_tick(is_valid=is_valid, date_str=date_str)
                if is_valid:
                    valid_ticks += 1
                elif res.get("rejection_reason"):
                    logger.warning(f"Tick rejected {sym}: {res['rejection_reason']}")

                if res.get("closed_candles", {}).get("5m"):
                    log_5m_diagnostics(sym)

                if res.get("generated_signal"):
                    logger.info(f"SIGNAL {sym}: {res['generated_signal']}")

                for pos in res.get("exited_positions") or []:
                    p = pos if isinstance(pos, dict) else pos.__dict__
                    phase9_session_engine.record_trade_closed(
                        gross_pnl=p.get("unrealized_pnl", 0.0),
                        exit_slippage=p.get("slippage_incurred", 0.0),
                        exit_charges=p.get("statutory_charges", 0.0),
                    )

                db = SessionLocal()
                try:
                    for op in db.query(PaperPosition).filter(
                        PaperPosition.symbol == sym, PaperPosition.status == "OPEN").all():
                        paper_engine.update_position_price(db, op.id, new_price=tick.ltp)
                except Exception as exc:
                    logger.warning(f"MTM update failed {sym}: {exc}")
                finally:
                    db.close()

            if any_live:
                last_live_quote_at = cur
            elif (cur - last_live_quote_at).total_seconds() > MAX_SILENT_SECONDS:
                msg = (f"❌ Session {session_id} ABORTED — no LIVE quotes for "
                       f"{MAX_SILENT_SECONDS}s (token expired? network?). Squaring off.")
                logger.error(msg)
                await telegram_alert(msg)
                break

            if iteration % 20 == 0:
                pf = live_streamer.position_manager.get_portfolio_summary()
                rem = max(0, int((target_end_ist - cur).total_seconds()))
                logger.info(
                    f"[{_fmt_ist(cur)} IST] {session_id} | ticks={valid_ticks} | "
                    f"open={pf.get('open_positions_count', 0)} | pnl=₹{pf.get('today_total_pnl', 0.0):.2f} | "
                    f"risk_left=₹{pf.get('daily_loss_remaining', 0.0):.2f} | {rem//60}m left"
                )

            await asyncio.sleep(poll_interval_sec)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Interrupted by operator. Squaring off...")

    # ---- 6. Square-off
    for pos in live_streamer.position_manager.get_open_positions():
        live_streamer.position_manager.square_off_position(pos.id, reason="MANDATORY_SQUARE_OFF_1515")
        phase9_session_engine.record_trade_closed(
            gross_pnl=pos.unrealized_pnl, exit_slippage=pos.slippage_incurred, exit_charges=pos.statutory_charges)

    closed_session = phase9_session_engine.close_session(reason="MANDATORY_SQUARE_OFF_1515") or session

    # ---- 7. Reports — only if we actually had data
    if valid_ticks == 0:
        msg = f"❌ Session {session_id} closed with ZERO valid ticks. No report generated; this is a feed failure, not a strategy result."
        logger.error(msg)
        await telegram_alert(msg)
        return 2

    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    dq_stats = live_streamer.data_quality_monitor.get_provider_summary() if hasattr(live_streamer, "data_quality_monitor") else None
    daily = Phase9ReportGenerator.generate_daily_report(session_data=closed_session, paper_trades=trades, data_quality_stats=dq_stats)
    cum = Phase9ReportGenerator.generate_cumulative_report()

    summary = (f"🏁 Session {session_id} done. ticks={valid_ticks} trades={len(trades)} "
               f"net=₹{closed_session.get('net_pnl', 0.0):.2f} verdict={cum['verdict']}")
    logger.info(summary)
    await telegram_alert(summary)

    print("\n" + "=" * 70)
    print("🏁 PAPER TRADING SESSION COMPLETE — REPORTS GENERATED")
    print(f"📅 {date_str} | 🆔 {session_id} | ticks {valid_ticks} | trades {len(trades)}")
    print(f"💰 Net P&L ₹{closed_session.get('net_pnl', 0.0):.2f}")
    print(f"📄 {daily['markdown_path']}\n📈 {cum['markdown_path']}\n⚖️ {cum['verdict']}")
    print("=" * 70 + "\n")
    return 0


def main():
    p = argparse.ArgumentParser(description="Run a 09:15-15:15 IST paper trading session (Angel One feed).")
    p.add_argument("--date", type=str, default=None)
    p.add_argument("--now", action="store_true", help="Start immediately without waiting for 09:15 IST.")
    p.add_argument("--duration-minutes", type=float, default=None)
    p.add_argument("--symbols", type=str, default=None, help="Comma-separated, e.g. RELIANCE,INFY,TCS")
    p.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between quote cycles (min 1.5).")
    p.add_argument("--allow-delayed-fallback", action="store_true",
                   help="Use Yahoo (15-min delayed) when Angel fails. OFF by default; delayed data is not live.")
    p.add_argument("--skip-history", action="store_true", help="Skip 5m history warm-up (testing only).")
    a = p.parse_args()

    syms = [s.strip().upper() for s in a.symbols.split(",")] if a.symbols else None
    code = asyncio.run(run_paper_session(
        target_date=a.date, start_now=a.now, duration_minutes=a.duration_minutes,
        symbols=syms, poll_interval_sec=a.poll_interval,
        allow_delayed_fallback=a.allow_delayed_fallback, skip_history=a.skip_history,
    ))
    sys.exit(code)


if __name__ == "__main__":
    main()
