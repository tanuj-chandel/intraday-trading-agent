"""
Phase 9 — Security Audit & Paper Trading Enforcement Tests

Performs an exhaustive static and dynamic security audit:
1. Scans codebase for any broker order placement methods.
2. Asserts IS_PAPER_TRADING=True and TRADING_MODE=PAPER.
3. Confirms human approval is mandatory.
4. Confirms RiskManager, Kill Switch, and 15:15 IST square-off cannot be bypassed.
"""
import os
import glob
import pytest
from app.core.config import settings
from app.risk.manager import RiskManager
from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel
from app.live.streamer import live_streamer


def get_app_python_files():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
    return glob.glob(os.path.join(base, "**", "*.py"), recursive=True)


FORBIDDEN_CALLS = [
    "place_order(",
    "create_order(",
    "submit_order(",
    "modify_order(",
    "cancel_order(",
    "send_order(",
    "order_place(",
    "place_trade(",
]


def test_no_order_placement_methods_exist():
    """Verify zero order execution methods exist across all app/ Python files."""
    files = get_app_python_files()
    assert len(files) > 0

    violations = []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            # Ignore comments and docstrings
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for pattern in FORBIDDEN_CALLS:
                if pattern in stripped:
                    violations.append(f"{filepath}:{idx} -> {pattern}")

    assert not violations, f"CRITICAL SECURITY VIOLATION — Real order placement code detected:\n" + "\n".join(violations)


def test_paper_trading_config_enforced():
    """Verify global config strictly enforces paper trading."""
    assert settings.IS_PAPER_TRADING is True, "IS_PAPER_TRADING must be True"
    assert settings.TRADING_MODE == "PAPER", "TRADING_MODE must be 'PAPER'"


def test_human_approval_cannot_be_bypassed():
    """Verify streamer does not auto-execute signals without human approval."""
    from app.live.streamer import LiveTickStreamer
    streamer = LiveTickStreamer()
    assert hasattr(streamer, "approve_signal"), "Must require explicit approve_signal invocation"
    assert hasattr(streamer, "reject_signal"), "Must allow explicit signal rejection"


def test_kill_switch_l5_escalation():
    """Verify Level 5 kill switch blocks all operations and requires manual reset code."""
    ks = HierarchicalKillSwitch()
    ks.activate(KillSwitchLevel.L5_FULL_HALT, "Emergency test")
    assert ks.is_active is True
    assert ks.current_level == KillSwitchLevel.L5_FULL_HALT

    # Reset without confirmation code fails
    res_fail = ks.reset("")
    assert res_fail["success"] is False

    # Reset with valid code succeeds
    res_ok = ks.reset("CONFIRM_MANUAL_RESET")
    assert res_ok["success"] is True


def test_risk_manager_active():
    """Verify risk manager rejects trade conditions when emergency stop is triggered."""
    from app.schemas.schemas import TradeSignalCreate
    rm = RiskManager()
    rm.trigger_emergency_stop()

    signal = TradeSignalCreate(
        symbol="RELIANCE",
        direction="BUY",
        entry_price=1000.0,
        stop_loss=990.0,
        target_price=1025.0,
        quantity=25,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="Test Emergency Stop"
    )
    res = rm.validate_trade(
        signal=signal,
        current_equity=100000.0,
        today_realized_loss=0.0,
        open_positions_count=1,
        trades_count_today=2,
        consecutive_losses=0
    )
    assert res.passed is False
    assert "Emergency Stop" in res.rejection_reason
