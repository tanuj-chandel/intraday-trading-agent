import pytest
from app.data.historical_loader import HistoricalDataLoader
from app.backtest.sensitivity import ParameterSensitivityAnalyzer

def test_parameter_sensitivity_matrix():
    df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")
    res = ParameterSensitivityAnalyzer.analyze(df, symbol="RELIANCE")

    assert res["total_combinations_tested"] >= 5
    assert "coefficient_of_variation" in res
    assert "stability_rating" in res
    assert "overfitting_risk" in res
    assert len(res["grid_results"]) > 0
