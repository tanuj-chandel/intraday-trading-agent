"""
Phase 9 — Statistical Evidence Engine

Calculates empirical statistical validation metrics:
- 1,000 to 10,000 iteration bootstrap 95% confidence intervals for win rate & expectancy
- Monte Carlo simulations of forward equity trajectories
- Maximum drawdown distribution
- Probability of consecutive losing streaks
- Probability of ruin
- Strict 5-tier sample size milestone labeling
"""
import math
import random
from typing import Dict, Any, List


class Phase9StatisticalEvidenceEngine:
    """
    Computes rigorous statistical evidence from live paper trading observations.
    Prevents premature declarations of statistical significance.
    """

    @classmethod
    def get_milestone_label(cls, sample_size: int) -> Dict[str, Any]:
        """Strict automated milestone gate."""
        n = int(sample_size)
        if n < 30:
            return {
                "stage": "INSUFFICIENT",
                "label": "Insufficient Sample (<30)",
                "next_milestone": 30,
                "progress_pct": round(n / 30 * 100, 1),
                "scientific_interpretation": "Sample size is too small to differentiate signal from market noise. Zero statistical conclusions permitted."
            }
        elif n < 100:
            return {
                "stage": "VERY PRELIMINARY",
                "label": "Very Preliminary Evidence (30–99)",
                "next_milestone": 100,
                "progress_pct": round(n / 100 * 100, 1),
                "scientific_interpretation": "Early indicative pattern. Standard errors remain broad; cannot rule out variance."
            }
        elif n < 300:
            return {
                "stage": "PRELIMINARY",
                "label": "Preliminary Evidence (100–299)",
                "next_milestone": 300,
                "progress_pct": round(n / 300 * 100, 1),
                "scientific_interpretation": "Preliminary empirical distribution formed. Outlier dependency and regime sensitivity must be tested."
            }
        elif n < 500:
            return {
                "stage": "EMPIRICAL",
                "label": "Empirical Evidence (300–499)",
                "next_milestone": 500,
                "progress_pct": round(n / 500 * 100, 1),
                "scientific_interpretation": "Robust statistical sample across varied market sessions. Statistical power adequate for formal hypothesis testing."
            }
        else:
            return {
                "stage": "HIGH-CONFIDENCE CANDIDATE",
                "label": "High-Confidence Candidate (500+)",
                "next_milestone": None,
                "progress_pct": 100.0,
                "scientific_interpretation": "High-confidence empirical paper sample. Candidate for institutional paper review. Real trading still requires separate capital clearance."
            }

    @classmethod
    def compute_evidence(cls, paper_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute full statistical battery: bootstrap CIs, Monte Carlo, and streak probabilities.
        """
        n = len(paper_trades)
        milestone = cls.get_milestone_label(n)

        if n == 0:
            return {
                "sample_size": 0,
                "milestone": milestone,
                "metrics": {},
                "bootstrap": {},
                "bootstrap_95ci": {},
                "monte_carlo": {},
                "monte_carlo_forward": {},
                "probabilities": {},
                "disclaimer": "PAPER TRADING ONLY — Zero real money orders."
            }

        pnls = [float(t.get("net_pnl", 0.0)) for t in paper_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        win_rate = (len(wins) / n * 100.0)

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = abs(sum(losses)) / len(losses) if losses else 0.0
        expectancy = (win_rate / 100.0 * avg_win) - ((1.0 - win_rate / 100.0) * avg_loss)

        gross_wins = sum(wins)
        gross_losses = abs(sum(losses))
        profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

        # 1. Bootstrap 95% Confidence Intervals (1,000 resamples)
        bootstrap_win_rates = []
        bootstrap_expectancies = []
        random.seed(42)  # Deterministic seed for reproducible testing

        num_bootstrap = 1000 if n >= 5 else 100
        for _ in range(num_bootstrap):
            sample = [random.choice(pnls) for _ in range(n)]
            s_wins = [x for x in sample if x > 0]
            s_losses = [x for x in sample if x <= 0]
            s_wr = (len(s_wins) / n * 100.0)
            s_aw = sum(s_wins) / len(s_wins) if s_wins else 0.0
            s_al = abs(sum(s_losses)) / len(s_losses) if s_losses else 0.0
            s_exp = (s_wr / 100.0 * s_aw) - ((1.0 - s_wr / 100.0) * s_al)
            bootstrap_win_rates.append(s_wr)
            bootstrap_expectancies.append(s_exp)

        bootstrap_win_rates.sort()
        bootstrap_expectancies.sort()

        ci_low_idx = int(num_bootstrap * 0.025)
        ci_high_idx = int(num_bootstrap * 0.975)

        wr_ci = (
            round(bootstrap_win_rates[ci_low_idx], 1),
            round(bootstrap_win_rates[ci_high_idx], 1),
        )
        exp_ci = (
            round(bootstrap_expectancies[ci_low_idx], 2),
            round(bootstrap_expectancies[ci_high_idx], 2),
        )

        # 2. Probability of Losing Streaks
        loss_prob = 1.0 - (win_rate / 100.0)
        p_3_losses = round((loss_prob ** 3) * 100.0, 2)
        p_5_losses = round((loss_prob ** 5) * 100.0, 2)
        p_8_losses = round((loss_prob ** 8) * 100.0, 2)

        # 3. Probability of Ruin Approximation (assuming 2% risk per trade on ₹100,000 capital)
        # Simplified formula: ((1 - A) / (1 + A)) ** (capital_units) where A = Edge
        if expectancy > 0 and avg_loss > 0:
            edge = expectancy / avg_loss
            # With ₹100,000 capital and ₹2,000 risk unit (50 units)
            units = 50
            ratio = (1.0 - min(0.9, edge)) / (1.0 + min(0.9, edge))
            p_ruin = round(max(0.0, min(100.0, (ratio ** units) * 100.0)), 2)
        else:
            p_ruin = 100.0 if expectancy <= 0 else 0.0

        # 4. Monte Carlo Max Drawdown Simulation (500 runs of 100 forward trades)
        mc_drawdowns = []
        for _ in range(500):
            running = 0.0
            peak = 0.0
            max_dd = 0.0
            for _ in range(100):
                sim_trade = random.choice(pnls)
                running += sim_trade
                if running > peak:
                    peak = running
                dd = peak - running
                if dd > max_dd:
                    max_dd = dd
            mc_drawdowns.append(max_dd)

        mc_drawdowns.sort()
        mc_median_dd = round(mc_drawdowns[int(len(mc_drawdowns) * 0.5)], 2)
        mc_p95_dd = round(mc_drawdowns[int(len(mc_drawdowns) * 0.95)], 2)

        return {
            "sample_size": n,
            "milestone": milestone,
            "metrics": {
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate_pct": round(win_rate, 2),
                "expectancy_inr": round(expectancy, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_win_inr": round(avg_win, 2),
                "avg_loss_inr": round(avg_loss, 2),
                "total_net_pnl": round(sum(pnls), 2),
            },
            "bootstrap_95ci": {
                "win_rate": {"low": wr_ci[0], "high": wr_ci[1]},
                "expectancy_inr": {"low": exp_ci[0], "high": exp_ci[1]},
                "iterations": num_bootstrap,
            },
            "monte_carlo_forward": {
                "median_max_drawdown_inr": mc_median_dd,
                "p95_max_drawdown_inr": mc_p95_dd,
                "simulations": 500,
                "forward_trades_per_run": 100,
            },
            "probabilities": {
                "prob_3_consecutive_losses_pct": p_3_losses,
                "prob_5_consecutive_losses_pct": p_5_losses,
                "prob_8_consecutive_losses_pct": p_8_losses,
                "prob_ruin_pct": p_ruin,
            },
            "disclaimer": "PAPER TRADING ONLY — Statistical calculations reflect paper trading simulations only."
        }
