import numpy as np
import random
from typing import List, Dict, Any

class EnhancedMonteCarloAnalyzer:
    """
    Enhanced Dual-Mode Monte Carlo Resampling Engine:
    Mode A: Bootstrap with replacement (1,000 resamples)
    Mode B: Trade-order reshuffling without replacement (1,000 permutations)
    """

    @classmethod
    def simulate_dual_mode(
        cls,
        trades: List[Dict[str, Any]],
        initial_capital: float = 100000.0,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        if not trades:
            return {
                "iterations": iterations,
                "mode_a_bootstrap": {"median_return_pct": 0.0, "p95_max_drawdown_pct": 0.0, "worst_drawdown_pct": 0.0},
                "mode_b_reshuffle": {"median_return_pct": 0.0, "p95_max_drawdown_pct": 0.0, "worst_drawdown_pct": 0.0},
                "max_consecutive_losing_streak": 0,
                "summary": "No trades available for Monte Carlo simulation."
            }

        pnls = [t.get("net_pnl", 0.0) for t in trades]
        n_trades = len(pnls)

        # MODE A: Bootstrap with replacement
        boot_returns = []
        boot_drawdowns = []

        for _ in range(iterations):
            sampled_pnls = [random.choice(pnls) for _ in range(n_trades)]
            equity = initial_capital
            peak = initial_capital
            max_dd = 0.0

            for p in sampled_pnls:
                equity += p
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

            boot_returns.append((equity - initial_capital) / initial_capital * 100.0)
            boot_drawdowns.append(max_dd)

        # MODE B: Reshuffle without replacement
        reshuffle_drawdowns = []
        for _ in range(iterations):
            shuffled = pnls.copy()
            random.shuffle(shuffled)
            equity = initial_capital
            peak = initial_capital
            max_dd = 0.0

            for p in shuffled:
                equity += p
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

            reshuffle_drawdowns.append(max_dd)

        # Max consecutive losses in original sequence
        max_losing_streak = 0
        current_streak = 0
        for p in pnls:
            if p < 0:
                current_streak += 1
                if current_streak > max_losing_streak:
                    max_losing_streak = current_streak
            else:
                current_streak = 0

        return {
            "iterations": iterations,
            "trades_resampled": n_trades,
            "mode_a_bootstrap": {
                "median_return_pct": round(float(np.median(boot_returns)), 2),
                "p05_return_pct": round(float(np.percentile(boot_returns, 5)), 2),
                "p95_return_pct": round(float(np.percentile(boot_returns, 95)), 2),
                "median_max_drawdown_pct": round(float(np.median(boot_drawdowns)), 2),
                "p95_max_drawdown_pct": round(float(np.percentile(boot_drawdowns, 95)), 2),
                "worst_simulated_drawdown_pct": round(float(max(boot_drawdowns)), 2)
            },
            "mode_b_reshuffle": {
                "median_max_drawdown_pct": round(float(np.median(reshuffle_drawdowns)), 2),
                "p95_max_drawdown_pct": round(float(np.percentile(reshuffle_drawdowns, 95)), 2),
                "worst_simulated_drawdown_pct": round(float(max(reshuffle_drawdowns)), 2)
            },
            "max_consecutive_losing_streak": max_losing_streak,
            "data_source_mode": "STATISTICAL MONTE CARLO SIMULATION (1,000 Permutations)",
            "summary": f"Across {iterations:,} bootstrap permutations, 95% of simulated runs experienced Max Drawdown under {np.percentile(boot_drawdowns, 95):.2f}%."
        }
