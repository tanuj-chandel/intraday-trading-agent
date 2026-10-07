import pytest
from app.data.historical_loader import HistoricalDataLoader
from app.backtest.rolling_walk_forward import RollingWalkForwardService

def test_rolling_walk_forward_pipeline():
    df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")
    res = RollingWalkForwardService.run_rolling_walk_forward(df, symbol="RELIANCE", windows_count=3)

    assert res["total_windows"] == 3
    assert len(res["rolling_windows"]) == 3
    assert "aggregate_wfe_ratio" in res
    assert "overall_stability" in res
