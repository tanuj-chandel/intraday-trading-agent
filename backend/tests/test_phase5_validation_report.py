import pytest
from app.backtest.validation_report import StrategyValidationReportGenerator

def test_validation_report_generation():
    bt_res = {
        "strategy_id": "VWAP_EMA_MOMENTUM_V1",
        "symbol": "RELIANCE",
        "initial_capital": 100000.0,
        "final_capital": 100500.0,
        "net_pnl": 500.0,
        "return_pct": 0.50,
        "total_trades": 10,
        "win_rate": 60.0,
        "profit_factor": 1.45,
        "expectancy": 50.0,
        "max_drawdown": 200.0,
        "max_drawdown_pct": 0.20,
        "total_charges": 65.0,
        "sharpe_ratio": 1.5,
        "sortino_ratio": 1.8
    }
    qualification = {
        "dataset_classification": "SAMPLE",
        "sample_size_rating": "INSUFFICIENT_SAMPLE",
        "profitability_classification": "NO_EDGE_OR_MARGINAL",
        "provenance_description": "Sample test dataset"
    }
    overfitting = {
        "risk_level": "LOW_RISK",
        "overfitting_risk_score": 12.5,
        "metrics_comparison": {"train_profit_factor": 1.5, "val_profit_factor": 1.45, "oos_profit_factor": 1.40, "oos_degradation_pct": 6.7}
    }
    walk_forward = {"walk_forward_efficiency_ratio": 0.93}
    monte_carlo = {
        "mode_a_bootstrap": {"median_max_drawdown_pct": 0.25, "p95_max_drawdown_pct": 0.35, "worst_simulated_drawdown_pct": 0.45},
        "max_consecutive_losing_streak": 2
    }

    report = StrategyValidationReportGenerator.generate_report(
        backtest_result=bt_res,
        qualification=qualification,
        overfitting=overfitting,
        walk_forward=walk_forward,
        monte_carlo=monte_carlo
    )

    assert "markdown_content" in report
    assert "Strategy Validation Audit Report" in report["markdown_content"]
    assert report["symbol"] == "RELIANCE"
    assert "qualification" in report
