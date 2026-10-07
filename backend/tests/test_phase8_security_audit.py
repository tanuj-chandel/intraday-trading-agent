"""
Phase 8 — Security Audit Tests
Verifies that no real-money order placement code exists anywhere in the system.
Tests the 5-tier data provenance system: UNCONFIGURED blocks signals.
"""
import os
import glob
import pytest
from app.live.quality_gate import DataProvenanceState, LiveDataQualityGate
import datetime


# ── Security: No Order Placement ─────────────────────────────────────────────

def get_all_python_files():
    """Get all Python files in the backend/app directory."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return glob.glob(os.path.join(base, "app", "**", "*.py"), recursive=True)


FORBIDDEN_PATTERNS = [
    "place_order(",
    "create_order(",
    "submit_order(",
    "execute_order(",
    "place_trade(",
    "send_order(",
    "order_place(",
]


def test_no_order_placement_anywhere():
    """CRITICAL: No real-money order placement code anywhere in app/."""
    all_py = get_all_python_files()
    assert len(all_py) > 0, "No Python files found to scan"

    violations = []
    for filepath in all_py:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in content:
                    # Check if it's in a comment or docstring (acceptable)
                    for lineno, line in enumerate(content.split("\n"), 1):
                        stripped = line.strip()
                        if pattern in stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'"):
                            violations.append(f"{filepath}:{lineno}: '{pattern}'")
        except Exception:
            continue

    assert not violations, (
        f"SECURITY VIOLATION: Real-money order placement code found:\n" +
        "\n".join(violations)
    )


def test_no_hardcoded_credentials():
    """Verify no real API keys are hardcoded in any Python file."""
    all_py = get_all_python_files()
    suspicious_patterns = [
        "ZERODHA_ACCESS_TOKEN = 'kite_",
        'ZERODHA_ACCESS_TOKEN = "kite_',
        "UPSTOX_ACCESS_TOKEN = 'up_",
        'UPSTOX_ACCESS_TOKEN = "up_',
        "ANGELONE_JWT_TOKEN = 'eyJ",  # JWT tokens start with eyJ
        'ANGELONE_JWT_TOKEN = "eyJ',
    ]
    violations = []
    for filepath in all_py:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for pattern in suspicious_patterns:
                if pattern in content:
                    violations.append(f"{filepath}: potential hardcoded credential '{pattern}'")
        except Exception:
            continue
    assert not violations, f"Potential hardcoded credentials:\n" + "\n".join(violations)


def test_paper_trading_flag_in_config():
    """Config must have IS_PAPER_TRADING=True and TRADING_MODE=PAPER."""
    from app.core.config import settings
    assert settings.IS_PAPER_TRADING is True, "IS_PAPER_TRADING must be True"
    assert settings.TRADING_MODE == "PAPER", "TRADING_MODE must be 'PAPER'"


# ── Provenance Gate: UNCONFIGURED Blocks Signals ─────────────────────────────

def test_unconfigured_state_blocks_signals():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=False,  # No credentials
    )
    assert result["status"] == DataProvenanceState.UNCONFIGURED
    assert result["can_generate_signals"] is False
    assert result["trading_enabled"] is False


def test_mock_state_blocks_signals():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=True,  # Mock provider
        has_credentials=True,
    )
    assert result["status"] == DataProvenanceState.MOCK
    assert result["can_generate_signals"] is False


def test_error_state_blocks_signals():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        provider_error="HTTP 401 Unauthorized",
    )
    assert result["status"] == DataProvenanceState.ERROR
    assert result["can_generate_signals"] is False


def test_invalid_price_blocks_signals():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        last_tick_price=0.0,
    )
    assert result["status"] == DataProvenanceState.INVALID
    assert result["can_generate_signals"] is False


def test_stale_data_blocks_signals():
    old_time = datetime.datetime.now() - datetime.timedelta(seconds=60)
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=old_time,
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        last_tick_price=2980.0,
    )
    assert result["status"] == DataProvenanceState.STALE
    assert result["can_generate_signals"] is False


def test_disconnected_state_blocks_signals():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=None,
        is_market_connected=False,
        is_mock_provider=False,
        has_credentials=True,
    )
    assert result["status"] == DataProvenanceState.DISCONNECTED
    assert result["can_generate_signals"] is False


def test_live_state_requires_all_conditions():
    """LIVE state (permits signals) requires: credentials + no mock + connected + fresh + valid price."""
    now = datetime.datetime.now()
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=now,
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        last_tick_price=2980.0,
    )
    assert result["status"] == DataProvenanceState.LIVE
    assert result["can_generate_signals"] is True


# ── Kill Switch Safety ────────────────────────────────────────────────────────

def test_kill_switch_level5_requires_confirmation():
    from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel
    ks = HierarchicalKillSwitch()
    ks.activate(KillSwitchLevel.L5_FULL_HALT, "emergency")
    # Reset without code should fail
    result = ks.reset("")
    assert result.get("success") is False
    # Reset with wrong code should fail
    result = ks.reset("WRONG_CODE")
    assert result.get("success") is False
    # Reset with correct code should succeed
    result = ks.reset("CONFIRM_MANUAL_RESET")
    assert result.get("success") is True


def test_kill_switch_escalation_only():
    from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel
    ks = HierarchicalKillSwitch()
    ks.activate(KillSwitchLevel.L3_CLOSE_ALL_POSITIONS, "test")
    # Trying to "activate" a lower level should not reduce
    ks.activate(KillSwitchLevel.L1_PAUSE_SIGNALS, "downgrade attempt")
    assert ks.current_level >= KillSwitchLevel.L3_CLOSE_ALL_POSITIONS
