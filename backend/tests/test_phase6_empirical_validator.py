import pytest
from app.backtest.phase6_validator import Phase6EmpiricalValidator

def test_phase6_empirical_validation_pipeline():
    res = Phase6EmpiricalValidator.execute_validation(symbol="RELIANCE", universe_id="LIQUID_TOP_10")

    assert "final_verdict" in res
    # On sample data, MUST report INSUFFICIENT DATA FOR VALIDATION
    assert res["final_verdict"] == "INSUFFICIENT DATA FOR VALIDATION"
    assert "frozen_baseline_config" in res
    assert "data_quality_audit" in res
    assert "stock_concentration" in res
    assert "trade_concentration" in res
    assert "slippage_grid" in res
    assert len(res["slippage_grid"]) == 6
    assert "monte_carlo" in res
