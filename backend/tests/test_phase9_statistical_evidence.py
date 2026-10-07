"""
Phase 9 — Statistical Evidence Tests

Tests milestone classification, bootstrap confidence intervals,
Monte Carlo drawdown simulations, and losing streak probabilities.
"""
import pytest
from app.phase9.statistical_evidence import Phase9StatisticalEvidenceEngine


def test_milestone_gates():
    """Verify exact 5-tier milestone classification."""
    assert Phase9StatisticalEvidenceEngine.get_milestone_label(15)["stage"] == "INSUFFICIENT"
    assert Phase9StatisticalEvidenceEngine.get_milestone_label(35)["stage"] == "VERY PRELIMINARY"
    assert Phase9StatisticalEvidenceEngine.get_milestone_label(120)["stage"] == "PRELIMINARY"
    assert Phase9StatisticalEvidenceEngine.get_milestone_label(350)["stage"] == "EMPIRICAL"
    assert Phase9StatisticalEvidenceEngine.get_milestone_label(550)["stage"] == "HIGH-CONFIDENCE CANDIDATE"


def test_bootstrap_confidence_intervals():
    trades = [
        {"net_pnl": 200.0},
        {"net_pnl": 300.0},
        {"net_pnl": -100.0},
        {"net_pnl": 250.0},
        {"net_pnl": -150.0},
    ] * 6  # 30 trades

    evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trades)
    assert evidence["sample_size"] == 30
    assert evidence["milestone"]["stage"] == "VERY PRELIMINARY"

    # Bootstrap 95% CI exists and has low < high
    boot = evidence["bootstrap_95ci"]
    assert boot["win_rate"]["low"] <= boot["win_rate"]["high"]
    assert boot["expectancy_inr"]["low"] <= boot["expectancy_inr"]["high"]


def test_monte_carlo_drawdown_simulation():
    trades = [
        {"net_pnl": 200.0},
        {"net_pnl": -100.0},
        {"net_pnl": 300.0},
        {"net_pnl": -200.0},
    ] * 10

    evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trades)
    mc = evidence["monte_carlo_forward"]
    assert mc["median_max_drawdown_inr"] >= 0
    assert mc["p95_max_drawdown_inr"] >= mc["median_max_drawdown_inr"]


def test_streak_probabilities():
    trades = [
        {"net_pnl": 100.0},
        {"net_pnl": -100.0},
    ] * 10  # 50% win rate

    evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trades)
    probs = evidence["probabilities"]
    # P(3 losses) at 50% = 0.5^3 = 12.5%
    assert abs(probs["prob_3_consecutive_losses_pct"] - 12.5) < 0.1
