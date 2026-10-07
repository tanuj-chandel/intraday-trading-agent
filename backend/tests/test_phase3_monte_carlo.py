import pytest
from app.backtest.monte_carlo import MonteCarloAnalyzer

def test_monte_carlo_resampling():
    sample_trades = [
        {"trade_id": 1, "net_pnl": 550.0},
        {"trade_id": 2, "net_pnl": -220.0},
        {"trade_id": 3, "net_pnl": 480.0},
        {"trade_id": 4, "net_pnl": -190.0},
        {"trade_id": 5, "net_pnl": 620.0}
    ]
    res = MonteCarloAnalyzer.simulate(sample_trades, initial_capital=100000.0, iterations=500)
    assert res["iterations"] == 500
    assert "median_max_drawdown_pct" in res
    assert "p95_max_drawdown_pct" in res
    assert "p99_max_drawdown_pct" in res
    assert res["p95_max_drawdown_pct"] >= 0.0
