import datetime
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.core.database import Base, engine, SessionLocal
from app.api.v1.api import api_router
from app.live.streamer import live_streamer
from app.live.data_types import LiveTick
from app.data.adapters.angelone_adapter import AngelOneSmartApiAdapter
from app.paper_trading.engine import PaperTradingEngine
from app.risk.manager import RiskManager
from app.models.models import (
    Stock, Trade, PaperPosition, TradeSignal,
    LiveSession, LiveSignalRecord, LivePositionRecord,
    SystemLog, Phase8TradeJournalRecord, Phase8Alert, Phase8TickStats,
    Phase9Session, Phase9Signal, Phase9TradeEvent, Phase9Statistics, Phase9DailyReport
)
from app.data.universe import EXPANDED_INDIAN_UNIVERSE
from app.data.live_market_provider import LiveNSEMarketDataProvider
from app.learning.learner import market_learner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing Database schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed stock universe if empty
        existing_stocks = db.query(Stock).count()
        if existing_stocks == 0:
            logger.info("Seeding Expanded Indian Stock Universe into database...")
            for s in EXPANDED_INDIAN_UNIVERSE:
                stock_obj = Stock(
                    symbol=s.symbol,
                    nse_symbol=s.nse_symbol,
                    company_name=s.company_name,
                    sector=s.sector,
                    industry=s.industry,
                    exchange=s.exchange,
                    index_name=s.index_name,
                    liquidity_classification=s.liquidity_classification,
                    avg_daily_volume=s.avg_daily_volume,
                    avg_daily_turnover_cr=s.avg_daily_turnover_cr,
                    lot_size=s.lot_size,
                    tick_size=s.tick_size,
                    is_active=s.is_active
                )
                db.add(stock_obj)
            db.commit()

        # Seed sample historical paper trades if empty for instant dashboard metrics
        existing_trades = db.query(Trade).count()
        if existing_trades == 0:
            logger.info("Seeding sample paper trades for performance visualization...")
            now = datetime.datetime.now()
            sample_trades = [
                Trade(
                    symbol="TATAMOTORS",
                    strategy="VWAP_EMA_Momentum_RVOL",
                    direction="BUY",
                    entry_price=1010.0,
                    exit_price=1030.0,
                    stop_loss=995.0,
                    target_price=1040.0,
                    quantity=30,
                    gross_pnl=600.0,
                    estimated_charges=38.40,
                    net_pnl=561.60,
                    holding_time_minutes=42.0,
                    reason_for_entry="VWAP Breakout + Volume Surge",
                    reason_for_exit="TARGET_HIT",
                    market_regime="TRENDING_UP",
                    score_at_entry=88.5,
                    entry_time=now - datetime.timedelta(hours=4),
                    exit_time=now - datetime.timedelta(hours=3, minutes=18)
                ),
                Trade(
                    symbol="RELIANCE",
                    strategy="VWAP_EMA_Momentum_RVOL",
                    direction="BUY",
                    entry_price=2950.0,
                    exit_price=2985.0,
                    stop_loss=2920.0,
                    target_price=3010.0,
                    quantity=15,
                    gross_pnl=525.0,
                    estimated_charges=44.10,
                    net_pnl=480.90,
                    holding_time_minutes=55.0,
                    reason_for_entry="EMA 9/21 Bullish Cross above VWAP",
                    reason_for_exit="TARGET_HIT",
                    market_regime="TRENDING_UP",
                    score_at_entry=91.0,
                    entry_time=now - datetime.timedelta(hours=3),
                    exit_time=now - datetime.timedelta(hours=2, minutes=5)
                ),
                Trade(
                    symbol="INFY",
                    strategy="VWAP_EMA_Momentum_RVOL",
                    direction="SELL",
                    entry_price=1830.0,
                    exit_price=1842.0,
                    stop_loss=1845.0,
                    target_price=1800.0,
                    quantity=20,
                    gross_pnl=-240.0,
                    estimated_charges=32.20,
                    net_pnl=-272.20,
                    holding_time_minutes=25.0,
                    reason_for_entry="VWAP Breakdown with negative IT news",
                    reason_for_exit="STOP_LOSS_HIT",
                    market_regime="SIDEWAYS",
                    score_at_entry=68.0,
                    entry_time=now - datetime.timedelta(hours=2),
                    exit_time=now - datetime.timedelta(hours=1, minutes=35)
                )
            ]
            for t in sample_trades:
                db.add(t)
            db.commit()

        # Crash recovery: reload open positions from DB and resume managing exits
        from app.execution.safety_service import execution_safety
        open_pos_db = db.query(PaperPosition).filter(PaperPosition.status == "OPEN").all()
        open_records = [
            {
                "id": p.id,
                "symbol": p.symbol,
                "side": getattr(p, "side", getattr(p, "direction", "BUY")),
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price or p.entry_price,
                "stop_loss": p.stop_loss,
                "target_price": p.target_price,
                "trailing_stop": getattr(p, "trailing_stop", getattr(p, "trailing_stop_loss", p.stop_loss)),
                "status": p.status,
                "opened_at": getattr(p, "opened_at", datetime.datetime.now())
            }
            for p in open_pos_db
        ]
        restored = execution_safety.recover_from_crash(open_records)
        if restored > 0:
            logger.info(f"Crash recovery restored {restored} open positions into active memory.")

        # Startup audit log
        log = SystemLog(
            level="INFO",
            module="SYSTEM_BOOT",
            message=f"{settings.PROJECT_NAME} initialized successfully in {settings.TRADING_MODE} TRADING MODE (Provider: {settings.MARKET_DATA_PROVIDER})."
        )
        db.add(log)
        db.commit()
    finally:
        db.close()

    # Daily broker session check
    try:
        from app.execution.safety_service import execution_safety
        await execution_safety.refresh_daily_token()
    except Exception as e:
        logger.warning(f"Initial broker token validation error: {e}")

    # Launch Real-Time Live Market Streamer Bridge & Adaptive Self-Learning in background
    stop_event = asyncio.Event()

    def get_dynamic_watchlist(count: int = 10) -> list[str]:
        day_num = datetime.datetime.now().timetuple().tm_yday
        sectors: dict[str, list[str]] = {}
        for s in EXPANDED_INDIAN_UNIVERSE:
            if s.symbol in ("M&M", "NIFTY 50", "BANK NIFTY"):
                continue
            sectors.setdefault(s.sector, []).append(s.symbol)
        wl = []
        for sec, syms in sorted(sectors.items()):
            if syms:
                wl.append(syms[day_num % len(syms)])
        drivers = ["RELIANCE", "HDFCBANK", "TCS", "INFY", "TATAMOTORS", "ICICIBANK", "SBIN", "BHARTIARTL", "LT", "BAJFINANCE", "TITAN", "ZOMATO", "BEL"]
        for d in drivers:
            if d not in wl and len(wl) < count:
                wl.append(d)
        return wl[:count]

    async def angelone_tick_worker():
        angel_adapter = AngelOneSmartApiAdapter()
        live_nse = LiveNSEMarketDataProvider()
        paper_engine = PaperTradingEngine(RiskManager())

        tracked_symbols = get_dynamic_watchlist(max_count := 10)
        live_streamer.connect("NSE_LIVE_FEED", is_mock=False, has_credentials=True)
        logger.info(f"Live Market Streamer connected with dynamic watchlist: {tracked_symbols}")

        loop_count = 0
        while not stop_event.is_set():
            try:
                now = datetime.datetime.now()
                loop_count += 1

                # Every 50 iterations, refresh watchlist and run self-learning optimization
                if loop_count % 50 == 0:
                    tracked_symbols = get_dynamic_watchlist(10)
                    db_learner = SessionLocal()
                    try:
                        market_learner.learn_from_database(db_learner)
                    except Exception as e:
                        logger.warning(f"Self-learning routine error: {e}")
                    finally:
                        db_learner.close()

                for sym in tracked_symbols:
                    if stop_event.is_set():
                        break

                    # 1. Try Angel One quote first if configured, else fallback to live NSE feed
                    quote_resp = None
                    if angel_adapter.is_configured:
                        quote_resp = await angel_adapter.get_quote(sym)

                    if not quote_resp or quote_resp.status != "LIVE":
                        quote_resp = await live_nse.get_quote_data(sym)

                    if quote_resp.status == "LIVE" and quote_resp.data:
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
                                timestamp=now,
                                data_source=quote_resp.source,
                                is_live=True
                            )
                            # Ingest into core strategy streamer (calculates candles, signals, SL/TP)
                            live_streamer.ingest_tick(tick)

                            # Sync open database positions MTM
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

                    await asyncio.sleep(0.5)

            except Exception as exc:
                logger.error(f"Error in live_tick_worker: {exc}")
                await asyncio.sleep(5)

            await asyncio.sleep(2.0)

    async def telegram_worker():
        from app.notifications.telegram_bot import telegram_notifier
        while not stop_event.is_set():
            try:
                if telegram_notifier.is_configured and telegram_notifier.enabled:
                    await telegram_notifier.poll_telegram_updates()
            except Exception as e:
                logger.debug(f"Telegram worker error: {e}")
            await asyncio.sleep(2.0)

    async def reconciliation_worker():
        from app.execution.safety_service import execution_safety
        while not stop_event.is_set():
            await asyncio.sleep(60.0)
            if stop_event.is_set():
                break
            try:
                await execution_safety.reconcile_positions()
            except Exception as e:
                logger.error(f"Reconciliation worker error: {e}")

    async def watchdog_worker():
        from app.execution.safety_service import execution_safety
        while not stop_event.is_set():
            await asyncio.sleep(30.0)
            if stop_event.is_set():
                break
            try:
                execution_safety.check_health_watchdog()
            except Exception as e:
                logger.error(f"Health watchdog worker error: {e}")

    poller_task = asyncio.create_task(angelone_tick_worker())
    telegram_task = asyncio.create_task(telegram_worker())
    reconciliation_task = asyncio.create_task(reconciliation_worker())
    watchdog_task = asyncio.create_task(watchdog_worker())

    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION} started with Two-Way Telegram Bot, Tick Poller, Reconciliation & Health Watchdog.")
    yield
    stop_event.set()
    poller_task.cancel()
    telegram_task.cancel()
    reconciliation_task.cancel()
    watchdog_task.cancel()
    logger.info("Shutting down trading agent...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI Intraday Trading Agent for Indian Stock Market (Paper Trading Mode)",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes for both /api and /api/v1 prefix
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "PAPER_TRADING_ONLY",
        "provider": settings.MARKET_DATA_PROVIDER,
        "docs_url": "/docs",
        "status": "online"
    }
