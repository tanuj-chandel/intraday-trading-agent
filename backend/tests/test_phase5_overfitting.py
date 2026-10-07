import pytest
from app.backtest.overfitting import OverfittingDetector

def test_overfitting_score_calculation():
    # Low degradation
    res_low = OverfittingDetector.calculate_overfitting_score(
        train_pf=1.5, val_pf=1.45, oos_pf=1.40, train_return=5.0, oos_return=4.8
    )
    assert res_low["risk_level"] == "LOW_RISK"
    assert res_low["overfitting_risk_score"] < 25.0

    # High degradation (severe drop in OOS)
    res_high = OverfittingDetector.calculate_overfitting_score(
        train_pf=2.5, val_pf=1.1, oos_pf=0.7, train_return=15.0, oos_return=-2.0
    )
    assert res_high["risk_level"] == "HIGH_OVERFITTING_RISK"
    assert res_high["overfitting_risk_score"] >= 50.0
