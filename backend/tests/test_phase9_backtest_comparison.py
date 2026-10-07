"""
Phase 9 — Backtest Comparison Tests

Tests drift calculation and classification of paper trading results
against the frozen Phase 6 backtest baseline.
"""
import pytest
from app.phase9.backtest_comparison import Phase9BacktestComparator


def test_comparison_no_trades():
    res = Phase9BacktestComparator.compare([])
    assert res["status"] == "NO_PAPER_TRADES"
    assert res["sample_size"] == 0
    assert res["verdict"] == "INSUFFICIENT LIVE PAPER DATA"


def test_comparison_with_trades():
    trades = [
        {"net_pnl": 350.0, "gross_pnl": 400.0, "total_cost": 50.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 40.0},
        {"net_pnl": 250.0, "gross_pnl": 300.0, "total_cost": 50.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 45.0},
        {"net_pnl": -150.0, "gross_pnl": -100.0, "total_cost": 50.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 30.0},
        {"net_pnl": 300.0, "gross_pnl": 350.0, "total_cost": 50.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 50.0},
    ] * 5  # 20 trades: 15 wins, 5 losses = 75% win rate

    res = Phase9BacktestComparator.compare(trades)
    assert res["sample_size"] == 20
    assert "comparison" in res
    assert "win_rate" in res["comparison"]
    assert "expectancy" in res["comparison"]
    assert "profit_factor" in res["comparison"]

    # Win rate is 75%, baseline is 55% -> positive drift
    assert res["comparison"]["win_rate"]["paper"] == 75.0
    assert res["comparison"]["win_rate"]["drift"] == 20.0
    assert res["comparison"]["win_rate"]["status"] == "PASS"


def test_comparison_degradation_detection():
    """Heavy losses must classify as DEGRADED or SEVERELY DEGRADED."""
    trades = [
        {"net_pnl": -300.0, "gross_pnl": -250.0, "total_cost": 50.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 25.0}
    ] * 15  # 15 losses, 0 wins

    res = Phase9BacktestComparator.compare(trades)
    assert res["classification"] in ("DEGRADED", "SEVERELY DEGRADED")
    assert res["comparison"]["win_rate"]["status"] == "FAIL"
