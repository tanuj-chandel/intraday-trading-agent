import pytest
from app.data.historical_loader import HistoricalDataLoader
from app.backtest.walk_forward import WalkForwardAnalyzer

def test_walk_forward_validation_pipeline():
    df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")
    res = WalkForwardAnalyzer.analyze(df, symbol="RELIANCE")

    assert res["validation_type"] == "WALK_FORWARD_CROSS_VALIDATION"
    assert "training_period" in res
    assert "validation_period" in res
    assert "out_of_sample_period" in res
    assert "walk_forward_efficiency_ratio" in res
    assert res["training_period"]["candle_count"] > 0
    assert res["out_of_sample_period"]["candle_count"] > 0
