"""
Phase 9 — Session Engine Tests

Tests session initialization, single-date boundary enforcement,
accounting increments, and session close logic.
"""
import pytest
from app.phase9.session_engine import Phase9SessionEngine


def test_start_session():
    engine = Phase9SessionEngine()
    sess = engine.start_session(trading_date="2026-09-04", provider="ZERODHA_KITE")
    assert sess["session_id"].startswith("SESS-2026-09-04-")
    assert sess["trading_date"] == "2026-09-04"
    assert sess["status"] == "ACTIVE"
    assert sess["provider"] == "ZERODHA_KITE"
    assert sess["valid_ticks"] == 0
    assert sess["net_pnl"] == 0.0


def test_cross_date_boundary_rejection():
    """Verify ticks from different dates are rejected or recorded as incidents."""
    engine = Phase9SessionEngine()
    engine.start_session(trading_date="2026-09-04")

    # Valid tick on same date
    engine.record_tick(is_valid=True, date_str="2026-09-04")
    curr = engine.get_current_session()
    assert curr["valid_ticks"] == 1
    assert curr["data_quality_incidents"] == 0

    # Cross-date tick from tomorrow or yesterday
    engine.record_tick(is_valid=True, date_str="2026-09-05")
    curr = engine.get_current_session()
    assert curr["valid_ticks"] == 1  # Not incremented
    assert curr["data_quality_incidents"] == 1  # Flagged incident


def test_session_accounting():
    """Verify session counters increment properly."""
    engine = Phase9SessionEngine()
    engine.start_session(trading_date="2026-09-04")

    engine.record_signal_generated()
    engine.record_signal_decision(approved=True)
    engine.record_signal_decision(approved=False)
    engine.record_trade_opened(slippage=5.0, charges=20.0)
    engine.record_trade_closed(gross_pnl=500.0, exit_slippage=5.0, exit_charges=40.0)

    curr = engine.get_current_session()
    assert curr["generated_signals"] == 1
    assert curr["approved_signals"] == 1
    assert curr["rejected_signals"] == 1
    assert curr["executed_paper_trades"] == 1
    assert curr["exits"] == 1
    assert curr["gross_pnl"] == 500.0
    # Net P&L = 500 - 60 (charges) - 10 (slippage) = 430
    assert curr["net_pnl"] == 430.0


def test_session_close():
    engine = Phase9SessionEngine()
    engine.start_session(trading_date="2026-09-04")
    closed = engine.close_session(reason="END_OF_DAY")
    assert closed is not None
    assert closed["status"] == "CLOSED"
    assert closed["close_reason"] == "END_OF_DAY"
    assert closed["market_close_time"] is not None
