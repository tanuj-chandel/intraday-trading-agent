import pytest
from app.backtest.qualification import DatasetQualificationService

def test_qualification_sample_dataset():
    q = DatasetQualificationService.qualify_dataset("SAMPLE_RELIANCE_5m.csv", total_candles=150)
    assert q["dataset_classification"] == "SAMPLE"
    assert q["is_sufficient_for_validation"] is False
    assert "INSUFFICIENT HISTORICAL DATA" in q["warning"]

def test_sample_size_classification():
    # Small trade count (<50)
    s_small = DatasetQualificationService.classify_sample_size(12)
    assert s_small["sample_size_rating"] == "INSUFFICIENT_SAMPLE"
    assert "INSUFFICIENT SAMPLE" in s_small["warning"]

    # Large trade count (350)
    s_large = DatasetQualificationService.classify_sample_size(350)
    assert s_large["sample_size_rating"] == "STRONGER_SAMPLE"
    assert s_large["warning"] is None

def test_statistical_edge_classification():
    # Negative Expectancy
    edge_neg = DatasetQualificationService.classify_statistical_edge(profit_factor=0.85, expectancy=-120.0, oos_degradation_pct=10.0, total_trades=100)
    assert edge_neg["profitability_classification"] == "NEGATIVE_EXPECTANCY"

    # Robust OOS Edge
    edge_rob = DatasetQualificationService.classify_statistical_edge(profit_factor=1.45, expectancy=180.0, oos_degradation_pct=15.0, total_trades=120)
    assert edge_rob["profitability_classification"] == "ROBUST_OOS_EDGE"
