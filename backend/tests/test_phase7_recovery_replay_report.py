import os
import datetime
import pytest
from app.live.recovery import CrashRecoveryService
from app.live.replay import SessionReplayService
from app.live.comparison import BacktestVsPaperComparator
from app.live.report import Phase7ReportGenerator
from app.live.position_manager import LivePositionManager
from app.live.data_types import LiveSignalItem

def test_recovery_replay_and_phase7_report():
    # 1. Crash Recovery
    pm = LivePositionManager()
    persisted = [{
        "id": 1, "symbol": "INFY", "side": "BUY", "quantity": 10, "entry_price": 1800.0,
        "current_price": 1810.0, "stop_loss": 1780.0, "target_price": 1840.0, "trailing_stop": 1780.0,
        "unrealized_pnl": 100.0, "unrealized_pnl_pct": 0.5, "status": "OPEN",
        "opened_at": datetime.datetime.now()
    }]
    rec = CrashRecoveryService.restore_session(pm, persisted)
    assert rec["restored_positions_count"] == 1
    assert len(pm.get_open_positions()) == 1

    # 2. Session Replay
    sig = LiveSignalItem(
        id=5, symbol="TCS", direction="BUY", entry_price=3900.0, stop_loss=3850.0,
        target_price=4000.0, quantity=5, risk_reward_ratio=2.0, strategy_score=85.0,
        status="EXECUTED", market_regime="TRENDING_UP",
        indicator_snapshot={"vwap": 3890.0, "rsi": 62.0}, data_freshness_seconds=0.5,
        created_at=datetime.datetime.now(), reason="Replay test"
    )
    rep = SessionReplayService.replay_signal_decision(sig)
    assert rep["signal_id"] == 5
    assert rep["indicator_state_at_entry"]["vwap"] == 3890.0

    # 3. Backtest vs Paper Comparator
    comp = BacktestVsPaperComparator.compare_metrics(
        backtest_metrics={"win_rate": 60.0, "net_pnl": 5000.0},
        paper_trades=[{"net_realized_pnl": 200.0, "slippage_incurred": 10.0}]
    )
    assert comp["paper_trades_count"] == 1
    assert "metrics_comparison" in comp

    # 4. Phase 7 Report Generator
    session_data = {
        "provider": "ZERODHA_KITE",
        "real_market_data_connected": True,
        "number_of_trading_sessions": 1,
        "number_of_paper_trades": 10,
        "net_realized_pnl": 1200.0,
        "win_rate": 60.0,
        "profit_factor": 1.5
    }
    p7_rep = Phase7ReportGenerator.generate_and_save(session_data, output_dir="reports")
    assert os.path.exists(p7_rep["markdown_path"])
    assert "PHASE 7 — REAL-TIME LIVE MARKET PAPER VALIDATION REPORT" in p7_rep["markdown_content"]
