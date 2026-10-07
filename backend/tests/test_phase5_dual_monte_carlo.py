import pytest
from app.backtest.monte_carlo_enhanced import EnhancedMonteCarloAnalyzer

def test_enhanced_dual_mode_monte_carlo():
    trades = [
        {"trade_id": 1, "net_pnl": 400.0},
        {"trade_id": 2, "net_pnl": -150.0},
        {"trade_id": 3, "net_pnl": 550.0},
        {"trade_id": 4, "net_pnl": -180.0}
    ]
    res = EnhancedMonteCarloAnalyzer.simulate_dual_mode(trades, initial_capital=100000.0, iterations=500)

    assert res["iterations"] == 500
    assert "mode_a_bootstrap" in res
    assert "mode_b_reshuffle" in res
    assert "median_return_pct" in res["mode_a_bootstrap"]
    assert "median_max_drawdown_pct" in res["mode_b_reshuffle"]
