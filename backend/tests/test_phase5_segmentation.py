import pytest
from app.backtest.segmentation import GranularSegmentationService

SAMPLE_TRADES = [
    {"trade_id": 1, "direction": "BUY", "entry_time": "2026-08-25T09:20:00", "entry_price": 2900.0, "quantity": 10, "gross_pnl": 500.0, "charges": 30.0, "net_pnl": 470.0, "market_regime": "TRENDING_BULLISH"},
    {"trade_id": 2, "direction": "SELL", "entry_time": "2026-08-25T13:40:00", "entry_price": 2920.0, "quantity": 10, "gross_pnl": -200.0, "charges": 30.0, "net_pnl": -230.0, "market_regime": "SIDEWAYS_CHOPPY"}
]

def test_market_regimes_breakdown():
    regimes = GranularSegmentationService.analyze_market_regimes(SAMPLE_TRADES)
    assert "regime_matrix" in regimes
    assert "TRENDING_BULLISH" in regimes["regime_matrix"]
    assert "SIDEWAYS_CHOPPY" in regimes["regime_matrix"]

def test_time_of_day_breakdown():
    tod = GranularSegmentationService.analyze_time_of_day(SAMPLE_TRADES)
    assert "time_of_day_breakdown" in tod
    assert len(tod["time_of_day_breakdown"]) == 7

def test_long_vs_short_breakdown():
    ls = GranularSegmentationService.analyze_long_vs_short(SAMPLE_TRADES)
    assert "long_trades" in ls
    assert "short_trades" in ls
    assert ls["long_trades"]["trades"] == 1
    assert ls["short_trades"]["trades"] == 1

def test_cost_and_slippage_sensitivity():
    cs = GranularSegmentationService.analyze_cost_and_slippage_sensitivity(SAMPLE_TRADES, initial_capital=100000.0)
    assert "cost_scenarios" in cs
    assert len(cs["cost_scenarios"]) == 3
    assert "slippage_matrix" in cs
    assert len(cs["slippage_matrix"]) == 5

def test_benchmark_comparisons():
    bench = GranularSegmentationService.compare_benchmarks(strategy_return_pct=0.24, strategy_pf=1.5, trades_count=2)
    assert "strategy" in bench
    assert "benchmarks" in bench
    assert len(bench["benchmarks"]) == 3
