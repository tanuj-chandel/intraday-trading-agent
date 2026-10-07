"""
Phase 9 — Controlled Paper Trading Pilot API Endpoints

Provides complete observational, session management, and empirical evidence APIs.
PAPER TRADING ONLY. Zero real-money order capability.
"""
import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from app.phase9.session_engine import phase9_session_engine
from app.phase9.provenance import Phase9ProvenanceEngine, Phase9ProvenanceState
from app.phase9.execution_realism import Phase9ExecutionEngine
from app.phase9.backtest_comparison import Phase9BacktestComparator
from app.phase9.statistical_evidence import Phase9StatisticalEvidenceEngine
from app.phase9.regime_analyzer import Phase9RegimeAnalyzer
from app.phase9.time_of_day_analyzer import Phase9TimeOfDayAnalyzer
from app.phase9.symbol_concentration import Phase9SymbolConcentrationEngine
from app.phase9.data_quality_impact import Phase9DataQualityImpactEngine
from app.phase9.verdict_engine import Phase9VerdictEngine
from app.phase9.reporting import Phase9ReportGenerator
from app.live.streamer import live_streamer

router = APIRouter()


@router.get("/status")
def get_phase9_status():
    """
    Get full Phase 9 pilot status, data mode badge, active session, and safety status.
    """
    session = phase9_session_engine.get_current_session()
    feed_status = live_streamer.get_status()
    gate = feed_status.get("data_quality_gate", {})
    state_str = gate.get("status", "MOCK")

    try:
        prov_state = Phase9ProvenanceState(state_str)
    except Exception:
        prov_state = Phase9ProvenanceState.MOCK

    ui_indicator = Phase9ProvenanceEngine.get_ui_indicator(prov_state)

    trades = Phase9ExecutionEngine.list_trades(limit=100)
    evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trades)

    return {
        "trading_mode": "PAPER_TRADING_ONLY",
        "real_order_execution": "DISABLED",
        "data_mode": ui_indicator,
        "provenance_state": prov_state.value,
        "active_session": session,
        "pilot_milestone": evidence.get("milestone", {}),
        "total_trades_count": len(trades),
        "disclaimer": "PAPER TRADING ONLY — Real-money order execution is permanently disabled.",
    }


@router.get("/session/current")
def get_current_session():
    """Get the currently active trading session."""
    session = phase9_session_engine.get_current_session()
    return {
        "session": session,
        "disclaimer": "PAPER TRADING ONLY."
    }


@router.get("/sessions")
def list_sessions(limit: int = Query(50, ge=1, le=200)):
    """List historic paper trading sessions."""
    sessions = phase9_session_engine.list_sessions(limit=limit)
    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
        "disclaimer": "PAPER TRADING ONLY."
    }


@router.get("/trades")
def list_trades(session_id: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=500)):
    """List executed paper trades with full itemized regulatory charges and slippage."""
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=limit)
    return {
        "total_trades": len(trades),
        "trades": trades,
        "accounting_equation": "GROSS P&L − TRANSACTION COST − SLIPPAGE = NET P&L",
        "disclaimer": "PAPER TRADING ONLY."
    }


@router.get("/statistics")
def get_statistical_evidence(session_id: Optional[str] = Query(None)):
    """
    Get full empirical evidence battery: bootstrap 95% CIs, Monte Carlo forward drawdowns,
    streak probabilities, and milestone gates.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    return Phase9StatisticalEvidenceEngine.compute_evidence(trades)


@router.get("/backtest-comparison")
def get_backtest_comparison(session_id: Optional[str] = Query(None)):
    """
    Compare Phase 9 paper performance against frozen Phase 6 backtest baseline.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    return Phase9BacktestComparator.compare(trades)


@router.get("/regime-performance")
def get_regime_performance(session_id: Optional[str] = Query(None)):
    """
    Performance attribution across 9 market regimes.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    return Phase9RegimeAnalyzer.analyze(trades)


@router.get("/time-performance")
def get_time_performance(session_id: Optional[str] = Query(None)):
    """
    Performance attribution across 5 intraday time-of-day slots.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    return Phase9TimeOfDayAnalyzer.analyze(trades)


@router.get("/concentration")
def get_concentration_analysis(session_id: Optional[str] = Query(None)):
    """
    Symbol concentration analysis and risk flag (Top 1 > 50%, Top 3 > 80%).
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    return Phase9SymbolConcentrationEngine.analyze(trades)


@router.get("/data-quality-impact")
def get_data_quality_impact(session_id: Optional[str] = Query(None)):
    """
    Analyze correlation between feed latency, rejected ticks, and execution slippage/P&L.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    dq_stats = live_streamer.data_quality_monitor.get_provider_summary() if hasattr(live_streamer, "data_quality_monitor") else None
    return Phase9DataQualityImpactEngine.analyze(trades, dq_stats)


@router.get("/verdict")
def get_scientific_verdict(session_id: Optional[str] = Query(None)):
    """
    Strict empirical validation verdict based strictly on trade count and statistical edge.
    """
    trades = Phase9ExecutionEngine.list_trades(session_id=session_id, limit=1000)
    evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trades)
    comparison = Phase9BacktestComparator.compare(trades)
    metrics = evidence.get("metrics", {})

    return Phase9VerdictEngine.determine_verdict(
        total_trades=len(trades),
        expectancy=metrics.get("expectancy_inr", 0.0),
        win_rate=metrics.get("win_rate_pct", 0.0),
        profit_factor=metrics.get("profit_factor", 0.0),
        reality_gap_verdict=comparison.get("classification", "WITHIN EXPECTED RANGE")
    )


@router.get("/report")
def get_report(report_type: str = Query("daily", pattern="^(daily|cumulative)$")):
    """
    Generate or download daily session or cumulative pilot report.
    """
    if report_type == "cumulative":
        return Phase9ReportGenerator.generate_cumulative_report()

    session = phase9_session_engine.get_current_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active session found to report.")

    trades = Phase9ExecutionEngine.list_trades(session_id=session["session_id"], limit=1000)
    dq_stats = live_streamer.data_quality_monitor.get_provider_summary() if hasattr(live_streamer, "data_quality_monitor") else None

    return Phase9ReportGenerator.generate_daily_report(
        session_data=session,
        paper_trades=trades,
        data_quality_stats=dq_stats
    )


@router.post("/session/start")
def start_session(
    provider: str = Query("ZERODHA_KITE"),
    trading_date: Optional[str] = Query(None)
):
    """
    Start a new controlled paper trading session. Closes any previous cross-date session.
    """
    session = phase9_session_engine.start_session(
        trading_date=trading_date,
        provider=provider
    )
    return {
        "success": True,
        "message": f"Started Paper Trading Session {session['session_id']} for {session['trading_date']}.",
        "session": session,
        "disclaimer": "PAPER TRADING ONLY — Real order placement disabled."
    }


@router.post("/session/close")
def close_session(reason: str = Query("MANUAL_CLOSE")):
    """
    Close the currently active session and automatically generate its 20-section daily report.
    """
    closed = phase9_session_engine.close_session(reason=reason)
    if not closed:
        raise HTTPException(status_code=400, detail="No active session to close.")

    # Auto-generate daily report on session close
    trades = Phase9ExecutionEngine.list_trades(session_id=closed["session_id"], limit=1000)
    dq_stats = live_streamer.data_quality_monitor.get_provider_summary() if hasattr(live_streamer, "data_quality_monitor") else None
    report_res = Phase9ReportGenerator.generate_daily_report(
        session_data=closed,
        paper_trades=trades,
        data_quality_stats=dq_stats
    )

    return {
        "success": True,
        "message": f"Session {closed['session_id']} closed successfully.",
        "session": closed,
        "report_generated": {
            "markdown_path": report_res["markdown_path"],
            "json_path": report_res["json_path"],
            "verdict": report_res["verdict"],
        },
        "disclaimer": "PAPER TRADING ONLY."
    }
