import datetime
import pytest
from app.live.data_types import LiveSignalItem
from app.live.execution import LivePaperExecutionEngine
from app.live.position_manager import LivePositionManager

def test_paper_execution_and_position_lifecycle():
    sig = LiveSignalItem(
        id=1,
        symbol="RELIANCE",
        direction="BUY",
        entry_price=2900.0,
        stop_loss=2880.0,
        target_price=2940.0,
        quantity=10,
        risk_reward_ratio=2.0,
        strategy_score=80.0,
        status="APPROVED",
        market_regime="TRENDING_UP",
        indicator_snapshot={},
        data_freshness_seconds=1.0,
        created_at=datetime.datetime.now(),
        reason="Test buy"
    )

    pos = LivePaperExecutionEngine.execute_paper_order(sig, current_market_price=2900.0, position_id=101)
    assert pos.id == 101
    assert pos.status == "OPEN"
    assert pos.statutory_charges > 0

    pm = LivePositionManager()
    pm.add_position(pos)

    # 1. Update price moving up
    pm.update_market_price("RELIANCE", 2920.0)
    assert pos.unrealized_pnl > 0

    # 2. Target Hit at 2945.0
    exited = pm.update_market_price("RELIANCE", 2945.0)
    assert len(exited) == 1
    assert exited[0].status == "CLOSED"
    assert exited[0].exit_reason == "TARGET_HIT"
    assert exited[0].net_realized_pnl > 0
