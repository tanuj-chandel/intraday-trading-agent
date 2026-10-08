import pytest
import datetime
import asyncio
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.execution.broker_base import PaperBroker, LiveBroker, OrderState
from app.execution.safety_service import ExecutionSafetyService
from app.live.data_types import LiveSignalItem
from app.live.streamer import live_streamer

@pytest.fixture
def sample_signal():
    return LiveSignalItem(
        id=101,
        symbol="TCS",
        direction="BUY",
        entry_price=3500.0,
        stop_loss=3465.0,
        target_price=3570.0,
        quantity=50,
        risk_reward_ratio=2.0,
        strategy_score=85.0,
        market_regime="TRENDING_UP",
        indicator_snapshot={},
        data_freshness_seconds=1.2,
        created_at=datetime.datetime.now(),
        reason="EMA breakout with strong volume"
    )

@pytest.mark.asyncio
async def test_sl_failure_triggers_immediate_liquidation_and_fails_closed(sample_signal):
    """If broker-side Stop-Loss placement fails, immediately exit position and alert."""
    broker = PaperBroker()
    broker.fail_next_sl = True
    safety = ExecutionSafetyService(broker=broker)

    result_pos = await safety.execute_entry_with_broker_sl(
        signal=sample_signal,
        current_market_price=3500.0,
        position_id=1
    )

    # Position must fail closed
    assert result_pos is None

    # Verify orders in broker:
    # 1. Entry order (FILLED)
    # 2. SL order (REJECTED)
    # 3. Emergency liquidation order (FILLED)
    orders = list(broker._orders.values())
    assert len(orders) == 3
    assert orders[0].side == "BUY" and orders[0].state == OrderState.FILLED
    assert orders[1].side == "SELL" and orders[1].state == OrderState.REJECTED
    assert orders[2].side == "SELL" and orders[2].idempotency_key == f"EMERGENCY_EXIT_{sample_signal.id}"

@pytest.mark.asyncio
async def test_partial_fill_adjusts_position_and_sl_quantity(sample_signal):
    """When broker executes a partial fill, SL and position quantity must match actual filled shares."""
    broker = PaperBroker()
    broker.partial_fill_next = True
    safety = ExecutionSafetyService(broker=broker)

    result_pos = await safety.execute_entry_with_broker_sl(
        signal=sample_signal,
        current_market_price=3500.0,
        position_id=1
    )

    expected_qty = sample_signal.quantity // 2  # 25
    assert result_pos is not None
    assert result_pos.quantity == expected_qty
    assert result_pos.status == "OPEN"

    # Verify SL order was placed for the partial quantity
    orders = list(broker._orders.values())
    sl_orders = [o for o in orders if o.order_type == "SL-M"]
    assert len(sl_orders) == 1
    assert sl_orders[0].quantity == expected_qty

@pytest.mark.asyncio
async def test_duplicate_signal_idempotency_prevents_double_order(sample_signal):
    """The same signal with same idempotency key must not place two entry orders."""
    broker = PaperBroker()
    safety = ExecutionSafetyService(broker=broker)

    order1 = await broker.simulate_broker_entry(
        symbol=sample_signal.symbol,
        side=sample_signal.direction,
        quantity=sample_signal.quantity,
        price=sample_signal.entry_price,
        idempotency_key=f"ENTRY_{sample_signal.id}_{sample_signal.symbol}"
    )

    order2 = await broker.simulate_broker_entry(
        symbol=sample_signal.symbol,
        side=sample_signal.direction,
        quantity=sample_signal.quantity,
        price=sample_signal.entry_price,
        idempotency_key=f"ENTRY_{sample_signal.id}_{sample_signal.symbol}"
    )

    assert order1.order_id == order2.order_id
    assert len(broker._orders) == 1

def test_health_watchdog_detects_stale_feed_and_triggers_level2_kill_switch():
    """If feed is stale > STALE_FEED_SECONDS, watchdog flags failure; 3 failures trigger Level 2 Kill Switch."""
    safety = ExecutionSafetyService()
    now = datetime.datetime.now()

    # Fresh tick: healthy
    safety.record_tick_timestamp("RELIANCE")
    status = safety.check_health_watchdog()
    assert status["healthy"] is True
    assert status["stale"] is False

    # Simulate stale tick (> 15 seconds old)
    safety.last_tick_time["RELIANCE"] = now - datetime.timedelta(seconds=20)
    
    with patch.object(live_streamer, "activate_kill_switch") as mock_ks:
        status1 = safety.check_health_watchdog()
        assert status1["stale"] is True
        assert status1["failure_count"] == 1
        mock_ks.assert_not_called()

        status2 = safety.check_health_watchdog()
        assert status2["failure_count"] == 2
        mock_ks.assert_not_called()

        status3 = safety.check_health_watchdog()
        assert status3["failure_count"] == 3
        # On 3rd failure, Level 2 Kill Switch triggered
        mock_ks.assert_called_once_with(2, reason="Health watchdog: Data feed persistently stale (> 45s)")

def test_hard_guard_live_trading_enabled_refuses_synthetic_data():
    """When LIVE_TRADING_ENABLED=True, starting on synthetic or mock data must raise RuntimeError."""
    safety = ExecutionSafetyService()
    with patch.object(settings, "LIVE_TRADING_ENABLED", True):
        with pytest.raises(RuntimeError, match="CRITICAL SAFETY ABORT"):
            safety.verify_live_startup_guard("YAHOO_FINANCE", is_mock=False)

        with pytest.raises(RuntimeError, match="CRITICAL SAFETY ABORT"):
            safety.verify_live_startup_guard("SYNTHETIC_FEED", is_mock=False)

        with pytest.raises(RuntimeError, match="CRITICAL SAFETY ABORT"):
            safety.verify_live_startup_guard("NSE_LIVE", is_mock=True)

def test_live_broker_refuses_execution_when_live_disabled():
    """LiveBroker stub raises PermissionError when LIVE_TRADING_ENABLED is False."""
    broker = LiveBroker()
    with pytest.raises(PermissionError, match="CRITICAL SAFETY VIOLATION"):
        asyncio.run(broker.simulate_broker_entry("INFY", "BUY", 10, 1500.0))
