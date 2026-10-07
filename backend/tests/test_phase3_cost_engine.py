import pytest
from app.backtest.cost_calculator import TransactionCostCalculator, TransactionCostConfig

def test_round_trip_transaction_charges():
    # Buy 100 shares @ ₹1,000, Sell @ ₹1,020 (Turnover = ₹2,02,000)
    res = TransactionCostCalculator.calculate_round_trip_costs(
        buy_price=1000.0,
        sell_price=1020.0,
        quantity=100
    )
    assert res["total_turnover"] == 202000.0
    assert res["brokerage"] > 0
    assert res["stt"] > 0  # 0.025% of 102,000 = ₹25.50
    assert res["exchange_charges"] > 0
    assert res["gst"] > 0
    assert res["stamp_duty"] > 0
    assert res["total_charges"] > 40.0

def test_slippage_application():
    # Slippage for BUY increases execution price
    buy_exec = TransactionCostCalculator.apply_slippage(1000.0, "BUY", slippage_pct=0.001)
    assert buy_exec == 1001.0

    # Slippage for SELL decreases execution price
    sell_exec = TransactionCostCalculator.apply_slippage(1000.0, "SELL", slippage_pct=0.001)
    assert sell_exec == 999.0
