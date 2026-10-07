"""
Phase 8 — Extended Live API Endpoints
Adds new Phase 8 endpoints while preserving ALL Phase 7 endpoints.
Paper Trading ONLY. No order placement.

New endpoints:
  GET /api/live/trade-journal
  GET /api/live/execution-quality
  GET /api/live/validation-progress
  GET /api/live/backtest-vs-paper
  GET /api/live/regime-performance
  GET /api/live/alerts
  GET /api/live/data-quality
  GET /api/live/concentration
  POST /api/live/connect
  POST /api/live/disconnect
"""
import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.live.streamer import live_streamer
from app.live.data_types import LiveTick, LiveSignalItem
from app.live.audit import LiveAuditLogger
from app.live.replay import SessionReplayService
from app.live.comparison import BacktestVsPaperComparator
from app.live.report import Phase7ReportGenerator
from app.live.trade_journal import trade_journal
from app.live.alerter import alert_engine, AlertSeverity
from app.live.backtest_loader import get_backtest_baseline
from app.live.reality_gap import RealityGapAnalyzer

router = APIRouter()

# ─── Phase 7 Endpoints (all preserved) ───────────────────────────────────────

@router.get("/status")
def get_live_status():
    return live_streamer.get_status()

@router.get("/data-health")
def get_live_data_health():
    status = live_streamer.get_status()
    return {
        "status": status["data_quality_gate"]["status"],
        "is_connected": status["is_connected"],
        "provider": status["provider_name"],
        "is_mock": status["is_mock"],
        "data_age_seconds": status["data_quality_gate"].get("data_age_seconds", 0.0),
        "gate_details": status["data_quality_gate"],
        "checked_at": datetime.datetime.now().isoformat()
    }

@router.get("/signals")
def get_live_signals():
    return live_streamer.signal_engine.get_pending_signals()

@router.get("/positions")
def get_live_positions(status: str = Query("OPEN")):
    if status.upper() == "CLOSED":
        return live_streamer.position_manager.get_closed_positions()
    return live_streamer.position_manager.get_open_positions()

@router.get("/performance")
def get_live_performance():
    closed = live_streamer.position_manager.get_closed_positions()
    total_trades = len(closed)
    wins = [p for p in closed if (p.net_realized_pnl or 0) > 0]
    win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0
    net_pnl = sum(p.net_realized_pnl or 0 for p in closed)
    charges = sum(p.statutory_charges for p in closed)
    slippage = sum(p.slippage_incurred for p in closed)
    return {
        "total_paper_trades": total_trades,
        "winning_trades": len(wins),
        "losing_trades": total_trades - len(wins),
        "win_rate_pct": round(win_rate, 1),
        "net_realized_pnl": round(net_pnl, 2),
        "total_charges": round(charges, 2),
        "total_slippage": round(slippage, 2),
        "portfolio_summary": live_streamer.position_manager.get_portfolio_summary(),
        "disclaimer": "PAPER TRADING SIMULATION ONLY. Real money orders disabled."
    }

@router.post("/signal/{signal_id}/approve")
def approve_live_signal(signal_id: int):
    sig = live_streamer.signal_engine.get_signal(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail=f"Signal #{signal_id} not found.")

    if sig.status in ("EXECUTED", "REJECTED", "EXPIRED", "CANCELLED"):
        return {
            "success": False,
            "message": f"Signal #{signal_id} has already been processed (status={sig.status}). Duplicate action ignored safely.",
            "status": sig.status
        }

    pos = live_streamer.approve_signal(signal_id)
    if not pos:
        updated_sig = live_streamer.signal_engine.get_signal(signal_id)
        reason = updated_sig.risk_notes if updated_sig else "Signal approval failed RiskManager, timeout, or price drift limits."
        return {
            "success": False,
            "message": f"Unable to approve signal #{signal_id}: {reason}",
            "status": updated_sig.status if updated_sig else "FAILED"
        }
    return {
        "success": True,
        "message": f"Signal #{signal_id} approved. Executed as Paper Position #{pos.id}.",
        "position": pos.model_dump()
    }

@router.post("/signal/{signal_id}/reject")
def reject_live_signal(signal_id: int, reason: str = Query("User rejected")):
    success = live_streamer.reject_signal(signal_id, reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail="Signal ID not found")
    return {"success": True, "message": f"Signal #{signal_id} rejected."}

@router.post("/emergency-stop")
def trigger_live_emergency_stop(reason: str = Query("Manual emergency stop triggered")):
    """Level 3 kill switch — backward-compatible emergency stop."""
    return live_streamer.trigger_emergency_stop(reason)

@router.post("/kill-switch/reset")
def reset_kill_switch(manual_operator_code: str = Query("")):
    return live_streamer.reset_kill_switch(manual_operator_code)

@router.post("/kill-switch/{level}")
def activate_kill_switch(level: int, reason: str = Query("Manual activation")):
    if level < 1 or level > 5:
        raise HTTPException(status_code=400, detail="Level must be 1–5")
    alert_engine.kill_switch_activated(level, reason)
    return live_streamer.activate_kill_switch(level, reason)

@router.get("/kill-switch/status")
def get_kill_switch_status():
    return {
        "status": live_streamer.kill_switch.get_status(),
        "activation_log": live_streamer.kill_switch.get_log()[-20:]
    }

@router.get("/audit")
def get_live_audit_log(limit: int = Query(50, ge=1, le=200)):
    return LiveAuditLogger.get_events(limit)

@router.get("/session")
def get_live_session():
    status = live_streamer.get_status()
    return {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "trading_mode": "PAPER_TRADING_ONLY",
        "provider": status["provider_name"],
        "real_orders_placed": 0,
        "is_mock": status["is_mock"],
        "strategy_version": "VWAP_EMA_MOMENTUM_V1",
        "open_positions": len(status["open_positions"]),
        "portfolio": status["portfolio_summary"],
        "kill_switch": status["kill_switch"],
        "reality_gap": status["reality_gap"]
    }

@router.get("/replay/{signal_id}")
def replay_live_signal(signal_id: int):
    sig = live_streamer.signal_engine.get_signal(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail=f"Signal #{signal_id} not found in session memory.")
    return SessionReplayService.replay_signal_decision(sig)

@router.post("/tick")
def ingest_live_tick(tick_data: Dict[str, Any]):
    if "timestamp" not in tick_data:
        tick_data["timestamp"] = datetime.datetime.now()
    tick = LiveTick(**tick_data)
    return live_streamer.ingest_tick(tick)

@router.post("/square-off")
def trigger_square_off():
    prices = {s: t.ltp for s, t in live_streamer.latest_ticks.items()}
    closed = live_streamer.position_manager.square_off_all_positions(prices, reason="15:15_MANDATORY_SQUARE_OFF")
    return {
        "square_off_triggered": True,
        "positions_closed": len(closed),
        "portfolio": live_streamer.position_manager.get_portfolio_summary()
    }

@router.get("/reality-gap")
def get_reality_gap_analysis():
    closed_trades = [p.model_dump() for p in live_streamer.position_manager.get_closed_positions()]
    backtest_metrics = get_backtest_baseline()
    analyzer = RealityGapAnalyzer()
    report = analyzer.analyze(backtest_metrics, closed_trades)
    return {
        "verdict": report.verdict,
        "verdict_explanation": report.verdict_explanation,
        "paper_trades_count": report.paper_trades_count,
        "backtest_source": backtest_metrics.get("source", "UNKNOWN"),
        "metrics": {
            "live_win_rate": report.live_win_rate,
            "backtest_win_rate": report.backtest_win_rate,
            "win_rate_delta": report.win_rate_delta,
            "live_profit_factor": report.live_profit_factor,
            "backtest_profit_factor": report.backtest_profit_factor,
            "profit_factor_delta": report.profit_factor_delta,
            "live_expectancy": report.live_expectancy,
            "backtest_expectancy": report.backtest_expectancy,
            "avg_slippage_per_trade_inr": report.avg_slippage_per_trade_inr,
            "consecutive_losses": report.consecutive_losses
        },
        "threshold_breaches": report.threshold_breaches,
        "is_sufficient_data": report.is_sufficient_data,
        "is_validated": report.is_validated,
        "disclaimer": "PAPER TRADING ONLY"
    }

@router.get("/report")
def get_phase7_report():
    closed = live_streamer.position_manager.get_closed_positions()
    total_trades = len(closed)
    wins = [p for p in closed if (p.net_realized_pnl or 0) > 0]
    pnl = sum(p.net_realized_pnl or 0 for p in closed)
    charges = sum(p.statutory_charges for p in closed)
    slippage = sum(p.slippage_incurred for p in closed)
    session_data = {
        "provider": live_streamer.provider_name,
        "real_market_data_connected": not live_streamer.is_mock and live_streamer.is_connected,
        "data_provenance": str(live_streamer.get_status()["data_quality_gate"].get("status", "MOCK")),
        "number_of_trading_sessions": 1,
        "number_of_paper_trades": total_trades,
        "starting_capital": getattr(settings, "INITIAL_CAPITAL", 500000.0),
        "net_realized_pnl": round(pnl, 2),
        "gross_pnl": round(pnl + charges, 2),
        "total_charges": round(charges, 2),
        "total_slippage": round(slippage, 2),
        "win_rate": (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0,
        "profit_factor": 1.0,
        "symbols_count": len(live_streamer.latest_ticks) or 10,
        "max_daily_loss_hit": False,
        "kill_switch_activated": live_streamer.kill_switch.is_active,
        "kill_switch_level": int(live_streamer.kill_switch.current_level),
        "paper_trades_list": [p.model_dump() for p in closed],
        "backtest_metrics": get_backtest_baseline(),
        "avg_slippage_per_trade": (slippage / total_trades) if total_trades > 0 else 0.0
    }
    report = Phase7ReportGenerator.generate_and_save(session_data)
    return {
        "report_paths": {"markdown": report["markdown_path"], "json": report["json_path"]},
        "verdict": report["verdict"],
        "markdown_content": report["markdown_content"],
        "session_data_summary": {k: v for k, v in session_data.items() if k != "paper_trades_list"}
    }


# ─── Phase 8 New Endpoints ────────────────────────────────────────────────────

@router.get("/trade-journal")
def get_trade_journal(limit: int = Query(100, ge=1, le=1000)):
    """Full paper trade journal with analytics. PAPER TRADING ONLY."""
    analytics = trade_journal.compute_analytics()
    entries = trade_journal.get_all_entries()[-limit:]
    return {
        "analytics": analytics,
        "entries": entries,
        "total_entries": len(trade_journal._entries),
        "disclaimer": "PAPER TRADING SIMULATION ONLY. Real money orders: 0 (STRICTLY DISABLED).",
    }

@router.get("/execution-quality")
def get_execution_quality():
    """Execution quality metrics: slippage, latency, fill variance."""
    closed = live_streamer.position_manager.get_closed_positions()
    n = len(closed)
    if n == 0:
        return {"status": "NO_TRADES_YET", "paper_trades": 0, "disclaimer": "PAPER TRADING ONLY"}

    slippages = [p.slippage_incurred for p in closed]
    avg_slip = sum(slippages) / n
    max_slip = max(slippages)
    pct_with_slip = sum(1 for s in slippages if s > 0) / n * 100.0

    # Check if data quality monitor available
    quality_summary = {}
    if hasattr(live_streamer, 'data_quality_monitor'):
        quality_summary = live_streamer.data_quality_monitor.get_provider_summary()

    return {
        "paper_trades_analyzed": n,
        "avg_slippage_per_trade_inr": round(avg_slip, 2),
        "max_slippage_inr": round(max_slip, 2),
        "pct_trades_with_slippage": round(pct_with_slip, 1),
        "total_slippage_inr": round(sum(slippages), 2),
        "data_quality": quality_summary,
        "disclaimer": "PAPER TRADING ONLY",
    }

@router.get("/validation-progress")
def get_validation_progress():
    """4-tier validation milestone progress: 30 → 100 → 300 → 500 trades."""
    closed = live_streamer.position_manager.get_closed_positions()
    n = len(closed)
    milestones = [30, 100, 300, 500]

    completed = [m for m in milestones if n >= m]
    next_m = next((m for m in milestones if n < m), None)

    if n < 30:
        stage = "INSUFFICIENT_LIVE_DATA"
        progress_pct = round(n / 30 * 100)
    elif n < 100:
        stage = "EARLY_PAPER_ASSESSMENT"
        progress_pct = round(n / 100 * 100)
    elif n < 300:
        stage = "PRELIMINARY_PAPER_ASSESSMENT"
        progress_pct = round(n / 300 * 100)
    elif n < 500:
        stage = "EMPIRICAL_PAPER_ASSESSMENT"
        progress_pct = round(n / 500 * 100)
    else:
        stage = "HIGH_CONFIDENCE_CANDIDATE"
        progress_pct = 100

    return {
        "paper_trades": n,
        "stage": stage,
        "progress_pct_to_next_milestone": progress_pct,
        "next_milestone": next_m,
        "completed_milestones": completed,
        "milestones": [
            {"trades": m, "completed": n >= m,
             "label": {30: "Early", 100: "Preliminary", 300: "Empirical", 500: "High Confidence"}[m]}
            for m in milestones
        ],
        "scientific_note": "Do NOT claim strategy validated until 500+ trades with no reality-gap breach.",
        "disclaimer": "PAPER TRADING ONLY"
    }

@router.get("/backtest-vs-paper")
def get_backtest_vs_paper():
    """Full Phase 6 backtest vs live paper comparison table."""
    closed = [p.model_dump() for p in live_streamer.position_manager.get_closed_positions()]
    backtest = get_backtest_baseline()
    comparison = BacktestVsPaperComparator.compare_metrics(backtest, closed)
    return {
        "comparison": comparison,
        "backtest_source": backtest.get("source", "UNKNOWN"),
        "frozen_strategy": "VWAP_EMA_MOMENTUM_V1",
        "disclaimer": "PAPER TRADING ONLY. Backtest results not guaranteed to repeat."
    }

@router.get("/regime-performance")
def get_regime_performance():
    """Paper trade performance broken down by market regime."""
    analytics = trade_journal.compute_analytics()
    regime_data = analytics.get("regime_performance", {})
    return {
        "regime_performance": regime_data,
        "total_trades": analytics.get("total_trades", 0),
        "note": "Performance by market regime. Identifies where strategy works best/worst.",
        "disclaimer": "PAPER TRADING ONLY"
    }

@router.get("/alerts")
def get_alerts(severity: Optional[str] = Query(None), active_only: bool = Query(False)):
    """Internal system alerts for data quality, risk, and operational events."""
    if active_only:
        sev = AlertSeverity(severity.upper()) if severity else None
        return {
            "alerts": alert_engine.get_active_alerts(sev),
            "summary": alert_engine.get_summary()
        }
    return {
        "alerts": alert_engine.get_all_alerts(limit=100),
        "summary": alert_engine.get_summary()
    }

@router.get("/data-quality")
def get_data_quality():
    """Live data quality metrics: tick validator stats, latency, drop rates."""
    provider_summary = {}
    symbol_stats = []
    tick_stats = {}

    if hasattr(live_streamer, 'data_quality_monitor'):
        provider_summary = live_streamer.data_quality_monitor.get_provider_summary()
        symbol_stats = live_streamer.data_quality_monitor.get_all_symbol_stats()

    if hasattr(live_streamer, 'tick_validator'):
        tick_stats = live_streamer.tick_validator.get_stats()

    return {
        "provider_health": provider_summary,
        "per_symbol_stats": symbol_stats,
        "tick_validator_stats": tick_stats,
        "data_provenance": live_streamer.get_status()["data_quality_gate"]["status"],
        "disclaimer": "PAPER TRADING ONLY"
    }

@router.get("/concentration")
def get_concentration_analysis():
    """Top-symbol concentration analysis for paper trades."""
    analytics = trade_journal.compute_analytics()
    concentration = analytics.get("symbol_concentration", [])
    n = analytics.get("total_trades", 0)

    top1 = concentration[0]["contribution_pct"] if concentration else 0.0
    top3 = sum(s["contribution_pct"] for s in concentration[:3])
    top5 = sum(s["contribution_pct"] for s in concentration[:5])

    return {
        "total_trades": n,
        "symbol_concentration": concentration,
        "top1_contribution_pct": round(top1, 1),
        "top3_contribution_pct": round(top3, 1),
        "top5_contribution_pct": round(top5, 1),
        "concentration_risk": "HIGH" if top1 > 50 else ("MEDIUM" if top3 > 70 else "LOW"),
        "disclaimer": "PAPER TRADING ONLY"
    }

@router.post("/connect")
def connect_live_provider(provider: str = Query("ZERODHA_KITE"), is_mock: bool = Query(True)):
    """Connect to a market data provider. is_mock=False requires credentials in .env"""
    from app.data.adapters.zerodha_adapter import ZerodhaKiteAdapter
    from app.data.adapters.upstox_adapter import UpstoxAdapter
    from app.data.adapters.angelone_adapter import AngelOneSmartApiAdapter

    has_creds = False
    connection_test = {"status": "UNCONFIGURED", "provider": provider}

    if provider.upper() in ("ZERODHA", "ZERODHA_KITE"):
        adapter = ZerodhaKiteAdapter()
        connection_test = adapter.test_connection()
        has_creds = adapter.is_configured
    elif provider.upper() == "UPSTOX":
        adapter = UpstoxAdapter()
        connection_test = adapter.test_connection()
        has_creds = adapter.is_configured
    elif provider.upper() in ("ANGEL_ONE", "ANGELONE"):
        adapter = AngelOneSmartApiAdapter()
        connection_test = adapter.test_connection()
        has_creds = adapter.is_configured

    # Only allow is_mock=False if credentials actually exist
    actual_is_mock = is_mock or not has_creds
    live_streamer.connect(provider=provider, is_mock=actual_is_mock, has_credentials=has_creds)

    return {
        "connected": True,
        "provider": provider,
        "is_mock": actual_is_mock,
        "has_credentials": has_creds,
        "connection_test": connection_test,
        "data_provenance": "UNCONFIGURED" if not has_creds else ("LIVE" if not actual_is_mock else "MOCK"),
        "real_orders_disabled": True,
        "paper_trading_only": True,
    }

@router.post("/disconnect")
def disconnect_live_provider(reason: str = Query("Manual disconnect")):
    """Disconnect from live data feed cleanly."""
    live_streamer.disconnect(reason)
    return {
        "disconnected": True,
        "reason": reason,
        "positions_open": len(live_streamer.position_manager.get_open_positions()),
        "warning": "Open positions may need manual square-off. Use POST /api/live/square-off."
    }

@router.get("/auto-approve")
def get_auto_approve_status():
    """Returns current auto-approval status and expiration."""
    return {
        "enabled": live_streamer.auto_approve_enabled,
        "is_active": live_streamer.is_auto_approve_active(),
        "expiry": live_streamer.auto_approve_expiry,
        "mode": "PAPER_TRADING_ONLY"
    }

@router.post("/auto-approve")
def toggle_auto_approve(
    enabled: bool = Query(True),
    duration_days: int = Query(5, ge=1, le=30)
):
    """Set auto-approval for paper trade execution with an expiration window."""
    expiry_dt = datetime.datetime.now() + datetime.timedelta(days=duration_days)
    expiry_iso = expiry_dt.isoformat()
    live_streamer.set_auto_approve(enabled=enabled, expiry_iso=expiry_iso)
    return {
        "success": True,
        "enabled": enabled,
        "is_active": live_streamer.is_auto_approve_active(),
        "expiry": expiry_iso,
        "days": duration_days,
        "message": f"Auto-approval {'ENABLED' if enabled else 'DISABLED'} for paper trades for the next {duration_days} days."
    }

@router.post("/learn")
def run_market_learning():
    """Triggers real-time market learning from completed trades and updates strategy parameters."""
    from app.learning.learner import market_learner
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        updated_knowledge = market_learner.learn_from_database(db)
        return {
            "success": True,
            "message": "Market knowledge updated successfully from live trade history.",
            "knowledge": updated_knowledge
        }
    finally:
        db.close()

@router.get("/knowledge")
def get_market_knowledge():
    """Returns current updated market knowledge, best performers, and adaptive parameters."""
    from app.learning.learner import market_learner
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return market_learner.learn_from_database(db)
    finally:
        db.close()


