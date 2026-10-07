import datetime
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.scheduler import IntradayScheduler
from app.data.data_quality import DataQualityService
from app.models.models import SystemLog
from app.schemas.schemas import SystemStatusResponse, EmergencyStopRequest
from app.risk.manager import RiskManager
from app.paper_trading.engine import PaperTradingEngine

router = APIRouter()
scheduler = IntradayScheduler()
risk_manager = RiskManager()
paper_engine = PaperTradingEngine(risk_manager)

@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    summary = paper_engine.get_portfolio_summary(db)
    market_phase = scheduler.get_market_session_phase()
    dq = DataQualityService.get_quality_report()
    
    return SystemStatusResponse(
        trading_mode=settings.TRADING_MODE,
        is_paper_trading=settings.IS_PAPER_TRADING,
        emergency_stop_triggered=risk_manager.emergency_stop_triggered or settings.EMERGENCY_STOP_TRIGGERED,
        market_data_provider=settings.MARKET_DATA_PROVIDER.upper(),
        data_quality_status=dq["overall_status"],
        portfolio_value=summary["total_capital"],
        cash_balance=summary["cash_balance"],
        today_realized_pnl=summary["realized_pnl_today"],
        today_unrealized_pnl=summary["unrealized_pnl_today"],
        today_total_pnl=summary["total_pnl_today"],
        daily_loss_remaining=summary["daily_loss_remaining"],
        open_positions_count=summary["open_positions_count"],
        trades_count_today=summary["trades_count_today"],
        server_time=datetime.datetime.now(),
        market_status=market_phase
    )

@router.post("/emergency-stop")
def trigger_emergency_stop(
    req: EmergencyStopRequest,
    db: Session = Depends(get_db)
):
    settings.EMERGENCY_STOP_TRIGGERED = True
    res = paper_engine.emergency_square_off_all(db, reason=req.reason)
    return res

@router.get("/schedule")
def get_schedule():
    return {
        "schedule": scheduler.get_schedule(),
        "current_phase": scheduler.get_market_session_phase()
    }

@router.get("/logs")
def get_system_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    return logs

@router.get("/go-live-checklist")
def get_go_live_checklist(db: Session = Depends(get_db)):
    """
    Evaluates rigorous production readiness criteria against real trading history:
    1. >= 150 completed paper trades
    2. Positive net expectancy after all statutory costs
    3. Max drawdown strictly below configurable limit
    4. Zero unresolved reconciliation or stale-feed watchdog incidents in last 10 trading days
    """
    from app.models.models import Trade, SystemLog
    from app.analytics.performance import PerformanceEngine

    trades = db.query(Trade).all()
    trade_count = len(trades)
    metrics = PerformanceEngine.calculate_metrics(db)

    # 1. Minimum trades
    min_trades_req = getattr(settings, "GO_LIVE_MIN_TRADES", 150)
    trades_pass = trade_count >= min_trades_req

    # 2. Positive expectancy
    expectancy_val = metrics.expectancy_per_trade
    expectancy_pass = (expectancy_val > 0.0) if trade_count > 0 else False

    # 3. Max drawdown
    max_dd_limit = getattr(settings, "GO_LIVE_MAX_DRAWDOWN_PCT", 5.0)
    dd_val = metrics.max_drawdown_pct
    dd_pass = (dd_val <= max_dd_limit) if trade_count > 0 else False

    # 4. Reconciliation and stale-feed incidents
    window_days = getattr(settings, "GO_LIVE_INCIDENT_WINDOW_DAYS", 10)
    cutoff = datetime.datetime.now() - datetime.timedelta(days=window_days)
    incidents = db.query(SystemLog).filter(
        SystemLog.timestamp >= cutoff,
        SystemLog.module.in_(["RECONCILIATION", "WATCHDOG", "HEALTH_WATCHDOG"]),
        SystemLog.level.in_(["WARNING", "ERROR"])
    ).all()
    incident_count = len(incidents)
    incidents_pass = incident_count == 0

    items = [
        {
            "id": "MIN_PAPER_TRADES",
            "name": "Sample Size Reliability",
            "description": f"At least {min_trades_req} completed paper trades with full lifecycle data.",
            "current_value": f"{trade_count} trades",
            "target": f"≥ {min_trades_req}",
            "status": "PASS" if trades_pass else "FAIL",
            "passed": trades_pass
        },
        {
            "id": "POSITIVE_EXPECTANCY",
            "name": "Net Statistical Edge",
            "description": "Positive net expectancy per trade after all statutory charges and slippage.",
            "current_value": f"₹{expectancy_val:,.2f} / trade",
            "target": "> ₹0.00",
            "status": "PASS" if expectancy_pass else "FAIL",
            "passed": expectancy_pass
        },
        {
            "id": "MAX_DRAWDOWN",
            "name": "Capital Drawdown Protection",
            "description": f"Historical equity curve max drawdown strictly below risk ceiling ({max_dd_limit}%).",
            "current_value": f"{dd_val:.2f}%",
            "target": f"≤ {max_dd_limit:.1f}%",
            "status": "PASS" if dd_pass else "FAIL",
            "passed": dd_pass
        },
        {
            "id": "INCIDENTS_ZERO",
            "name": "Execution Layer Stability",
            "description": f"No unresolved broker reconciliation or stale data feed incidents in last {window_days} days.",
            "current_value": f"{incident_count} incidents",
            "target": "0 incidents",
            "status": "PASS" if incidents_pass else "FAIL",
            "passed": incidents_pass
        }
    ]

    all_passed = all(item["passed"] for item in items)

    return {
        "overall_status": "READY" if all_passed else "NOT_READY",
        "all_passed": all_passed,
        "live_trading_enabled": getattr(settings, "LIVE_TRADING_ENABLED", False),
        "is_paper_trading": getattr(settings, "IS_PAPER_TRADING", True),
        "total_trades": trade_count,
        "items": items
    }

@router.post("/toggle-live-trading")
def toggle_live_trading(payload: Dict[str, bool], db: Session = Depends(get_db)):
    """
    Safely toggles live order execution.
    Refuses with HTTP 400 if any checklist criteria fails.
    """
    from fastapi import HTTPException
    enable = payload.get("enable", False)

    if enable:
        checklist = get_go_live_checklist(db)
        if not checklist["all_passed"]:
            failed = [i["name"] for i in checklist["items"] if not i["passed"]]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot enable LIVE TRADING: Go-live checklist failed on: {', '.join(failed)}"
            )

        # Verification of live feed
        if getattr(settings, "MARKET_DATA_PROVIDER", "mock").lower() in ["mock", "synthetic", "yahoo"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot enable LIVE TRADING: Real broker feed required (synthetic/mock feeds strictly prohibited in live mode)."
            )

        settings.LIVE_TRADING_ENABLED = True
        return {"success": True, "live_trading_enabled": True, "message": "Live trading mode activated safely."}
    else:
        settings.LIVE_TRADING_ENABLED = False
        return {"success": True, "live_trading_enabled": False, "message": "Live trading disabled. Operating in paper trading mode."}

@router.post("/trigger-eod-report")
async def trigger_eod_report():
    """
    Manually triggers generation and dispatch of the 15:45 IST End-of-Day report via Telegram.
    """
    from app.notifications.telegram_bot import telegram_notifier
    res = await telegram_notifier.send_end_of_day_report()
    return res

