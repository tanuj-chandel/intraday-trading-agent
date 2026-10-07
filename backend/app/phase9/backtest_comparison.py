"""
Phase 9 — Paper vs Backtest Comparison Engine

Rigorous empirical comparison between the frozen Phase 6 backtest baseline
(VWAP_EMA_MOMENTUM_V1) and live Phase 9 paper trading observations.

Calculates drift in expectancy, win rate, profit factor, drawdown, and slippage.
Classifies performance: BETTER THAN BACKTEST, WITHIN EXPECTED RANGE, DEGRADED, SEVERELY DEGRADED.
"""
from typing import Dict, Any, List
from app.live.backtest_loader import get_backtest_baseline


class Phase9BacktestComparator:
    """
    Compares live paper trading performance against the frozen Phase 6 backtest.
    """

    @classmethod
    def compare(cls, paper_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare list of paper trades against frozen Phase 6 baseline.
        """
        baseline = get_backtest_baseline()
        n = len(paper_trades)

        if n == 0:
            return {
                "status": "NO_PAPER_TRADES",
                "sample_size": 0,
                "baseline_source": baseline.get("source", "UNKNOWN"),
                "strategy_version": "VWAP_EMA_MOMENTUM_V1",
                "comparison": {},
                "verdict": "INSUFFICIENT LIVE PAPER DATA",
                "disclaimer": "PAPER TRADING ONLY — Baseline frozen from Phase 6."
            }

        # Calculate Paper Trading Metrics
        wins = [t for t in paper_trades if t.get("net_pnl", 0.0) > 0]
        losses = [t for t in paper_trades if t.get("net_pnl", 0.0) <= 0]
        win_rate = (len(wins) / n * 100.0) if n > 0 else 0.0

        gross_pnl = sum(t.get("gross_pnl", 0.0) for t in paper_trades)
        net_pnl = sum(t.get("net_pnl", 0.0) for t in paper_trades)
        total_costs = sum(t.get("total_cost", 0.0) for t in paper_trades)
        total_slippage = sum(t.get("entry_slippage", 0.0) + t.get("exit_slippage", 0.0) for t in paper_trades)

        avg_win = (sum(t.get("net_pnl", 0.0) for t in wins) / len(wins)) if wins else 0.0
        avg_loss = (abs(sum(t.get("net_pnl", 0.0) for t in losses)) / len(losses)) if losses else 0.0
        loss_rate = 1.0 - (win_rate / 100.0)
        expectancy = (win_rate / 100.0 * avg_win) - (loss_rate * avg_loss)

        gross_wins = sum(t.get("net_pnl", 0.0) for t in wins)
        gross_losses = abs(sum(t.get("net_pnl", 0.0) for t in losses))
        profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

        # Drawdown calculation
        running = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in paper_trades:
            running += t.get("net_pnl", 0.0)
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd

        avg_hold = sum(t.get("holding_minutes", 0.0) for t in paper_trades) / n

        # Baseline metrics from Phase 6
        b_win_rate = float(baseline.get("win_rate", 55.0))
        b_expectancy = float(baseline.get("expectancy", 150.0))
        b_profit_factor = float(baseline.get("profit_factor", 1.5))
        b_avg_win = float(baseline.get("avg_win_inr", 350.0))
        b_avg_loss = float(baseline.get("avg_loss_inr", 200.0))
        b_max_dd_pct = float(baseline.get("max_drawdown_pct", 8.5))

        # Calculate Drifts
        win_rate_drift = round(win_rate - b_win_rate, 2)
        expectancy_drift = round(expectancy - b_expectancy, 2)
        pf_drift = round(profit_factor - b_profit_factor, 2)

        # Classification
        # Severely degraded: win rate > 15% below baseline OR PF < 0.8 OR expectancy < -50
        # Degraded: win rate > 8% below baseline OR PF < 1.1 OR expectancy < 0
        # Better: expectancy > baseline and win_rate >= baseline
        # Within expected: inside statistical boundary
        if n < 10:
            classification = "INSUFFICIENT_SAMPLE_FOR_CLASSIFICATION"
        elif win_rate_drift < -15.0 or profit_factor < 0.8 or expectancy < -50.0:
            classification = "SEVERELY DEGRADED"
        elif win_rate_drift < -8.0 or profit_factor < 1.1 or expectancy < 0.0:
            classification = "DEGRADED"
        elif expectancy > b_expectancy and win_rate >= b_win_rate:
            classification = "BETTER THAN BACKTEST"
        else:
            classification = "WITHIN EXPECTED RANGE"

        return {
            "sample_size": n,
            "baseline_source": baseline.get("source", "UNKNOWN"),
            "strategy_version": "VWAP_EMA_MOMENTUM_V1",
            "classification": classification,
            "comparison": {
                "win_rate": {
                    "backtest": b_win_rate,
                    "paper": round(win_rate, 2),
                    "drift": win_rate_drift,
                    "status": "PASS" if win_rate_drift >= -5.0 else ("WARN" if win_rate_drift >= -15.0 else "FAIL")
                },
                "expectancy": {
                    "backtest": b_expectancy,
                    "paper": round(expectancy, 2),
                    "drift": expectancy_drift,
                    "status": "PASS" if expectancy_drift >= -20.0 else ("WARN" if expectancy >= 0 else "FAIL")
                },
                "profit_factor": {
                    "backtest": b_profit_factor,
                    "paper": round(profit_factor, 2),
                    "drift": pf_drift,
                    "status": "PASS" if profit_factor >= 1.2 else ("WARN" if profit_factor >= 1.0 else "FAIL")
                },
                "avg_win": {
                    "backtest": b_avg_win,
                    "paper": round(avg_win, 2),
                },
                "avg_loss": {
                    "backtest": b_avg_loss,
                    "paper": round(avg_loss, 2),
                },
                "max_drawdown_inr": {
                    "paper": round(max_dd, 2),
                },
                "holding_time_minutes": {
                    "backtest": baseline.get("avg_hold_time_minutes", 45.0),
                    "paper": round(avg_hold, 1),
                },
                "financials": {
                    "gross_pnl": round(gross_pnl, 2),
                    "transaction_costs": round(total_costs, 2),
                    "slippage": round(total_slippage, 2),
                    "net_pnl": round(net_pnl, 2),
                }
            },
            "disclaimer": "PAPER TRADING ONLY — Real-money order execution is strictly disabled."
        }
