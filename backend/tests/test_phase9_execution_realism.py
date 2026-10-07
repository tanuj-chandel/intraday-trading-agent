"""
Phase 9 — Execution Realism Tests

Tests realistic fill prices, Indian statutory charges computation,
slippage models, and the equation: GROSS P&L - TRANSACTION COST - SLIPPAGE = NET P&L.
"""
import pytest
from app.phase9.execution_realism import (
    Phase9CostCalculator,
    Phase9ExecutionEngine,
)


def test_cost_calculator_all_charges():
    """Verify all Indian statutory charge components are calculated."""
    charges = Phase9CostCalculator.calculate_charges(buy_price=2980.0, sell_price=3010.0, quantity=10)
    assert "brokerage" in charges
    assert "stt" in charges
    assert "exchange_charges" in charges
    assert "sebi_charges" in charges
    assert "gst" in charges
    assert "stamp_duty" in charges
    assert "total_cost" in charges

    # Brokerage is ₹40 flat for 2 executed legs
    assert charges["brokerage"] == 40.0
    # Total cost must be sum of components
    expected_sum = round(
        charges["brokerage"] + charges["stt"] + charges["exchange_charges"] +
        charges["sebi_charges"] + charges["gst"] + charges["stamp_duty"], 2
    )
    assert charges["total_cost"] == expected_sum


def test_simulate_entry_fill_slippage():
    """Buy fills at or above intended; Sell fills at or below intended."""
    # BUY
    buy_fill, buy_slip = Phase9ExecutionEngine.simulate_entry_fill(
        direction="BUY", intended_price=1000.0, ask=1000.50
    )
    assert buy_fill == 1000.50
    assert buy_slip == 0.50

    # SELL
    sell_fill, sell_slip = Phase9ExecutionEngine.simulate_entry_fill(
        direction="SELL", intended_price=1000.0, bid=999.40
    )
    assert sell_fill == 999.40
    assert sell_slip == 0.60


def test_trade_pnl_accounting_equation():
    """Verify Gross - Costs = Net."""
    pnl = Phase9ExecutionEngine.compute_trade_pnl(
        direction="BUY",
        intended_entry=1000.0,
        fill_entry=1000.50,
        intended_exit=1020.0,
        fill_exit=1019.50,
        quantity=10
    )

    gross = pnl["gross_pnl"]
    net = pnl["net_pnl"]
    cost = pnl["total_cost"]

    # Fill exit (1019.50) - Fill entry (1000.50) = 19.00 * 10 = 190.00 Gross
    assert gross == 190.0
    assert net == round(gross - cost, 2)
    assert pnl["total_slippage"] == 10.0  # 5 entry slip + 5 exit slip


def test_record_completed_trade():
    trade = Phase9ExecutionEngine.record_completed_trade(
        session_id="SESS-2026-09-04-001",
        symbol="INFY",
        direction="BUY",
        intended_entry_price=1700.0,
        simulated_fill_price=1700.50,
        intended_exit_price=1720.0,
        simulated_exit_price=1719.50,
        quantity=20,
        latency_ms=25.0,
        mfe=450.0,
        mae=50.0,
        market_regime="TRENDING_UP",
        time_of_day_bucket="10:00–11:30"
    )

    assert trade["trade_id"] > 0
    assert trade["symbol"] == "INFY"
    assert trade["gross_pnl"] > 0
    assert trade["net_pnl"] < trade["gross_pnl"]  # Costs deducted
    assert trade["mfe"] == 450.0
    assert trade["mae"] == 50.0

    # Retrieve from DB list
    trades = Phase9ExecutionEngine.list_trades(session_id="SESS-2026-09-04-001")
    assert any(t["symbol"] == "INFY" for t in trades)
