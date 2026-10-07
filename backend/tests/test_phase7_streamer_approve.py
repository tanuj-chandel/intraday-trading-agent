"""
Tests for Phase 7 streamer approve_signal() flow — verifies Bug B1 fix.
approve_signal() must use RiskManager.validate_trade() without raising AttributeError.
"""
import datetime
import pytest
from unittest.mock import patch, MagicMock
from app.live.streamer import LiveTickStreamer
from app.live.data_types import LiveTick, LiveSignalItem


def _make_streamer() -> LiveTickStreamer:
    streamer = LiveTickStreamer()
    streamer.connect(provider="TEST", is_mock=False, has_credentials=True)
    return streamer


def _make_signal(signal_id: int = 1, symbol: str = "RELIANCE") -> LiveSignalItem:
    return LiveSignalItem(
        id=signal_id,
        symbol=symbol,
        direction="BUY",
        entry_price=2950.0,
        stop_loss=2906.5,
        target_price=3080.0,
        quantity=3,
        strategy_name="VWAP_EMA_MOMENTUM_V1",
        strategy_score=78.5,
        reason="EMA crossover + RVOL > 1.15",
        risk_reward_ratio=3.0,
        market_regime="BULLISH",
        data_freshness_seconds=1.2,
        indicator_snapshot={"ema_fast": 2951.0, "ema_slow": 2940.0},
        status="PENDING",
        risk_passed=False,
        risk_notes=None,
        created_at=datetime.datetime.now()
    )


class TestApproveSignalFlow:
    def test_approve_signal_does_not_raise_attribute_error(self):
        """Bug B1 fix: approve_signal() must not raise AttributeError on RiskManager."""
        streamer = _make_streamer()
        sig = _make_signal(signal_id=10)
        streamer.signal_engine._pending_signals[10] = sig

        # inject a market tick so fill price is available
        tick = LiveTick(
            symbol="RELIANCE", ltp=2950.0, open=2940.0, high=2960.0,
            low=2935.0, close=2950.0, volume=5000,
            bid=2949.5, ask=2950.5, spread=1.0,
            timestamp=datetime.datetime.now()
        )
        streamer.latest_ticks["RELIANCE"] = tick

        # Must not raise AttributeError
        try:
            pos = streamer.approve_signal(10)
            # pos may be None if RiskManager rejects (that's fine)
        except AttributeError as e:
            pytest.fail(f"approve_signal() raised AttributeError: {e}")

    def test_approve_unknown_signal_returns_none(self):
        """Approving a non-existent signal ID must return None, not crash."""
        streamer = _make_streamer()
        pos = streamer.approve_signal(999)
        assert pos is None

    def test_approve_already_executed_signal_returns_none(self):
        """Re-approving an already-executed signal must return None."""
        streamer = _make_streamer()
        sig = _make_signal(signal_id=20)
        sig.status = "EXECUTED"
        streamer.signal_engine._pending_signals[20] = sig
        pos = streamer.approve_signal(20)
        assert pos is None

    def test_reject_signal_marks_as_rejected(self):
        """reject_signal() must mark the signal status as REJECTED."""
        streamer = _make_streamer()
        sig = _make_signal(signal_id=30)
        streamer.signal_engine._pending_signals[30] = sig
        result = streamer.reject_signal(30, reason="Testing rejection")
        assert result is True
        sig_after = streamer.signal_engine.get_signal(30)
        assert sig_after.status == "REJECTED"

    def test_reject_unknown_signal_returns_false(self):
        streamer = _make_streamer()
        result = streamer.reject_signal(9999)
        assert result is False


class TestKillSwitchIntegration:
    def test_streamer_has_kill_switch(self):
        """Streamer must expose a kill_switch attribute with 5-level support."""
        streamer = _make_streamer()
        from app.live.kill_switch import HierarchicalKillSwitch
        assert isinstance(streamer.kill_switch, HierarchicalKillSwitch)
        assert streamer.kill_switch.can_generate_signals() is True

    def test_activate_level1_via_streamer(self):
        streamer = _make_streamer()
        result = streamer.activate_kill_switch(1, "Test pause")
        assert result["success"] is True
        assert streamer.kill_switch.can_generate_signals() is False

    def test_trigger_emergency_stop_is_level3(self):
        """trigger_emergency_stop() must delegate to Level 3 kill switch."""
        streamer = _make_streamer()
        streamer.trigger_emergency_stop("Testing")
        from app.live.kill_switch import KillSwitchLevel
        assert streamer.kill_switch.current_level == KillSwitchLevel.L3_CLOSE_ALL_POSITIONS

    def test_get_status_includes_kill_switch(self):
        streamer = _make_streamer()
        status = streamer.get_status()
        assert "kill_switch" in status
        assert "reality_gap" in status


class TestRealityGapIntegration:
    def test_streamer_has_reality_gap_analyzer(self):
        streamer = _make_streamer()
        from app.live.reality_gap import RealityGapAnalyzer
        assert isinstance(streamer.reality_gap, RealityGapAnalyzer)

    def test_reality_gap_in_status_with_no_trades(self):
        streamer = _make_streamer()
        status = streamer.get_status()
        rg = status["reality_gap"]
        assert "verdict" in rg
        assert rg["paper_trades"] == 0
        assert rg["is_sufficient_data"] is False
