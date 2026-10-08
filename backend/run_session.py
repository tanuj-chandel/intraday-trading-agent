"""
AI Intraday Trading Agent — Autonomous Paper Trading Session Runner
File: backend/run_session.py

Starts a controlled paper trading session at 09:15 IST, runs until 15:15 IST square-off,
records empirical execution evidence, generates the 20-section daily session report
in reports/phase9/, and automatically recalibrates the cumulative pilot report.

Supports standalone command-line execution and Windows Task Scheduler automated triggers.
PAPER TRADING SIMULATION ONLY — Real-money order execution is permanently disabled.
"""

import os
import sys
import time
import argparse
import asyncio
import datetime
from typing import List, Optional
import pytz

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.config import settings
from app.core.logging import logger
from app.core.database import Base, engine, SessionLocal
from app.models.models import Stock, PaperPosition
from app.data.universe import EXPANDED_INDIAN_UNIVERSE
from app.data.adapters.angelone_adapter import AngelOneSmartApiAdapter
from app.data.live_market_provider import LiveNSEMarketDataProvider
from app.paper_trading.engine import PaperTradingEngine
from app.risk.manager import RiskManager
from app.live.streamer import live_streamer
from app.live.data_types import LiveTick
from app.phase9.session_engine import phase9_session_engine
from app.phase9.execution_realism import Phase9ExecutionEngine
from app.phase9.reporting import Phase9ReportGenerator

IST = pytz.timezone("Asia/Kolkata")


def get_default_watchlist(count: int = 10) -> List[str]:
    """Select high-liquidity Nifty symbols for the trading session."""
    drivers = [
        "RELIANCE", "HDFCBANK", "TCS", "INFY", "TATAMOTORS",
        "ICICIBANK", "SBIN", "BHARTIARTL", "LT", "BAJFINANCE",
        "TITAN", "SUNPHARMA", "VEDL"
    ]
    return drivers[:count]


async def run_paper_session(
    target_date: Optional[str] = None,
    start_now: bool = False,
    duration_minutes: Optional[float] = None,
    symbols: Optional[List[str]] = None,
    poll_interval_sec: float = 2.0,
):
    """
    Main autonomous session loop from 09:15 to 15:15 IST.
    """
    print("=" * 70)
    print("🚀 AI INTRADAY TRADING AGENT (INDIA) — PAPER SESSION RUNNER")
    print("   Mandatory Safety: PAPER TRADING ONLY | Real Orders: DISABLED")
    print("=" * 70)

    # 1. Database Schema Pre-flight
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # 2. Timing & Market Hours Setup (Asia/Kolkata)
    now_ist = datetime.datetime.now(tz=IST)
    date_str = target_date or now_ist.strftime("%Y-%m-%d")
    watchlist = symbols or get_default_watchlist(10)

    market_open_ist = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    square_off_ist = now_ist.replace(hour=15, minute=15, second=0, microsecond=0)

    if duration_minutes is not None:
        target_end_ist = now_ist + datetime.timedelta(minutes=duration_minutes)
        logger.info(f"Custom session duration specified: {duration_minutes} minutes (Ending at {target_end_ist.strftime('%H:%M:%S')} IST).")
    else:
        target_end_ist = square_off_ist

    # Check whether we need to wait for 09:15 IST
    if not start_now and now_ist < market_open_ist and duration_minutes is None:
        wait_seconds = (market_open_ist - now_ist).total_seconds()
        logger.info(f"Current time is {now_ist.strftime('%H:%M:%S')} IST. Waiting {wait_seconds / 60:.1f} minutes until market open (09:15 IST)...")
        while datetime.datetime.now(tz=IST) < market_open_ist:
            rem = (market_open_ist - datetime.datetime.now(tz=IST)).total_seconds()
            if int(rem) % 60 == 0 or rem < 60:
                print(f"⏳ Waiting for market open (09:15 IST): {int(rem)}s remaining...", end="\r", flush=True)
            await asyncio.sleep(1.0)
        print()

    # Check if market has already closed for the day
    now_ist = datetime.datetime.now(tz=IST)
    if not start_now and duration_minutes is None and now_ist >= square_off_ist:
        logger.warning(
            f"Current time ({now_ist.strftime('%H:%M:%S')} IST) is after 15:15 IST square-off. "
            "Generating reports for the existing day or use --now / --duration-minutes for a simulated session."
        )
        report_res = Phase9ReportGenerator.generate_cumulative_report()
        print(f"✅ Cumulative Pilot Report updated: {report_res['json_path']}")
        return

    # 3. Initialize Phase 9 Session
    session = phase9_session_engine.start_session(
        trading_date=date_str,
        provider=settings.MARKET_DATA_PROVIDER,
        symbols=watchlist
    )
    session_id = session["session_id"]
    logger.info(f"Started Phase 9 Session {session_id} for date {date_str}.")

    # 4. Connect Live Streamer & Enable Autonomous Signal Approval
    angel_adapter = AngelOneSmartApiAdapter()
    live_nse = LiveNSEMarketDataProvider()
    paper_engine = PaperTradingEngine(RiskManager())

    live_streamer.connect("NSE_LIVE_FEED", is_mock=False, has_credentials=angel_adapter.is_configured)
    # Enable autonomous approval for today's session
    live_streamer.set_auto_approve(True, expiry_iso=target_end_ist.isoformat())
    logger.info(f"Auto-approval armed for session {session_id} through {target_end_ist.strftime('%H:%M:%S')} IST.")

    # 5. Active Market Loop
    logger.info(f"Entering active session loop. Monitoring {len(watchlist)} symbols: {watchlist}")
    iteration = 0
    reported_trades_count = 0

    try:
        while True:
            cur_time_ist = datetime.datetime.now(tz=IST)
            if cur_time_ist >= target_end_ist:
                logger.info(f"Target session end reached at {cur_time_ist.strftime('%H:%M:%S')} IST. Initiating square-off.")
                break

            iteration += 1

            for sym in watchlist:
                # Fetch quote
                quote_resp = None
                if angel_adapter.is_configured:
                    try:
                        quote_resp = await angel_adapter.get_quote(sym)
                    except Exception as e:
                        logger.debug(f"Angel One quote error for {sym}: {e}")

                if not quote_resp or quote_resp.status != "LIVE":
                    try:
                        quote_resp = await live_nse.get_quote_data(sym)
                    except Exception as e:
                        logger.debug(f"Live NSE quote error for {sym}: {e}")

                if quote_resp and quote_resp.status == "LIVE" and quote_resp.data:
                    d = quote_resp.data
                    ltp = float(d.get("ltp", 0.0))
                    if ltp > 0:
                        tick = LiveTick(
                            symbol=sym,
                            ltp=ltp,
                            open=float(d.get("open", ltp)),
                            high=float(d.get("high", ltp)),
                            low=float(d.get("low", ltp)),
                            close=float(d.get("close", ltp)),
                            volume=int(d.get("volume", 0)),
                            bid=float(d.get("bid", round(ltp * 0.9998, 2))),
                            ask=float(d.get("ask", round(ltp * 1.0002, 2))),
                            spread=float(d.get("spread", 0.0)),
                            timestamp=datetime.datetime.now(),
                            data_source=quote_resp.source,
                            is_live=True
                        )

                        # Ingest tick into strategy streamer
                        res = live_streamer.ingest_tick(tick)
                        phase9_session_engine.record_tick(is_valid=True, date_str=date_str)

                        # Track newly exited positions and record to Phase 9 accounting
                        if res.get("exited_positions"):
                            for pos in res["exited_positions"]:
                                p_obj = pos if isinstance(pos, dict) else pos.__dict__
                                phase9_session_engine.record_trade_closed(
                                    gross_pnl=p_obj.get("unrealized_pnl", 0.0),
                                    exit_slippage=p_obj.get("slippage_incurred", 0.0),
                                    exit_charges=p_obj.get("statutory_charges", 0.0)
                                )

                        # Sync open DB positions MTM
                        db_session = SessionLocal()
                        try:
                            open_pos = db_session.query(PaperPosition).filter(
                                PaperPosition.symbol == sym,
                                PaperPosition.status == "OPEN"
                            ).all()
                            for op in open_pos:
                                paper_engine.update_position_price(db_session, op.id, new_price=ltp)
                        except Exception:
                            pass
                        finally:
                            db_session.close()

                await asyncio.sleep(0.3)

            # Periodic status log
            if iteration % 20 == 0:
                portfolio = live_streamer.position_manager.get_portfolio_summary()
                open_cnt = portfolio.get("open_positions_count", 0)
                tot_pnl = portfolio.get("today_total_pnl", 0.0)
                rem_loss = portfolio.get("daily_loss_remaining", 0.0)
                time_rem = max(0, int((target_end_ist - cur_time_ist).total_seconds()))
                logger.info(
                    f"[{cur_time_ist.strftime('%H:%M:%S')} IST] Active Session {session_id} | "
                    f"Open Positions: {open_cnt} | Today Total PnL: ₹{tot_pnl:.2f} | "
                    f"Risk Floor Remaining: ₹{rem_loss:.2f} | Time Left: {time_rem // 60}m {time_rem % 60}s"
                )

            await asyncio.sleep(poll_interval_sec)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Session interrupted by operator. Executing graceful square-off...")

    # 6. Mandatory 15:15 IST Square-Off
    logger.info("Executing mandatory end-of-session square-off across all open positions...")
    open_positions = live_streamer.position_manager.get_open_positions()
    for pos in open_positions:
        live_streamer.position_manager.square_off_position(pos.id, reason="MANDATORY_SQUARE_OFF_1515")
        phase9_session_engine.record_trade_closed(
            gross_pnl=pos.unrealized_pnl,
            exit_slippage=pos.slippage_incurred,
            exit_charges=pos.statutory_charges
        )

    # 7. Close Session
    closed_session = phase9_session_engine.close_session(reason="MANDATORY_SQUARE_OFF_1515") or session
    logger.info(f"Phase 9 Session {session_id} closed successfully.")

    # 8. Generate Reports
    logger.info("Generating daily session report and updating cumulative pilot report...")
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    dq_stats = (
        live_streamer.data_quality_monitor.get_provider_summary()
        if hasattr(live_streamer, "data_quality_monitor") else None
    )

    daily_report = Phase9ReportGenerator.generate_daily_report(
        session_data=closed_session,
        paper_trades=trades,
        data_quality_stats=dq_stats
    )

    cum_report = Phase9ReportGenerator.generate_cumulative_report()

    print("\n" + "=" * 70)
    print("🏁 PAPER TRADING SESSION COMPLETE — REPORTS GENERATED")
    print("=" * 70)
    print(f"📅 Trading Date:            {date_str}")
    print(f"🆔 Session ID:               {session_id}")
    print(f"📊 Completed Paper Trades:   {len(trades)}")
    print(f"💰 Session Net P&L:          ₹{closed_session.get('net_pnl', 0.0):.2f}")
    print(f"📄 Daily Session Report:     {daily_report['markdown_path']}")
    print(f"📈 Cumulative Pilot Report:  {cum_report['markdown_path']}")
    print(f"⚖️ Scientific Verdict:       {cum_report['verdict']}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run an autonomous 09:15 - 15:15 IST paper trading session and generate Phase 9 validation reports."
    )
    parser.add_argument("--date", type=str, default=None, help="Trading date (YYYY-MM-DD). Defaults to today in IST.")
    parser.add_argument("--now", action="store_true", help="Start session immediately without waiting for 09:15 IST.")
    parser.add_argument("--duration-minutes", type=float, default=None, help="Run session for N minutes (useful for testing or dry-runs).")
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated symbols to monitor (e.g. RELIANCE,INFY,TCS).")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Quote polling interval in seconds (default: 2.0).")

    args = parser.parse_args()

    symbol_list = [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else None

    asyncio.run(
        run_paper_session(
            target_date=args.date,
            start_now=args.now,
            duration_minutes=args.duration_minutes,
            symbols=symbol_list,
            poll_interval_sec=args.poll_interval,
        )
    )


if __name__ == "__main__":
    main()
