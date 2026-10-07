from typing import Dict, Any, List

class BacktestVsPaperComparator:
    """
    Compares theoretical backtest expectations against real-world live paper trading execution metrics.
    Highlights slippage drift, fill variance, and execution anomalies.
    """

    @classmethod
    def compare_metrics(
        cls,
        backtest_metrics: Dict[str, Any],
        paper_trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not paper_trades:
            return {
                "paper_trades_count": 0,
                "status": "NO_LIVE_PAPER_TRADES_RECORDED",
                "comparison_note": "Awaiting live market session paper executions."
            }

        total_paper = len(paper_trades)
        wins = [t for t in paper_trades if t.get("net_realized_pnl", 0) > 0]
        paper_win_rate = round((len(wins) / total_paper) * 100.0, 1)
        paper_pnl = sum(t.get("net_realized_pnl", 0) for t in paper_trades)
        avg_slippage = sum(t.get("slippage_incurred", 0) for t in paper_trades) / total_paper

        bt_win_rate = backtest_metrics.get("win_rate", 50.0)
        bt_expected_slippage = backtest_metrics.get("slippage_pct", 0.05)

        return {
            "paper_trades_count": total_paper,
            "metrics_comparison": {
                "win_rate": {
                    "backtest_expected": bt_win_rate,
                    "live_paper_achieved": paper_win_rate,
                    "variance": round(paper_win_rate - bt_win_rate, 1)
                },
                "net_pnl": {
                    "backtest_sample": backtest_metrics.get("net_pnl", 0.0),
                    "live_paper_realized": round(paper_pnl, 2)
                },
                "average_slippage_inr": round(avg_slippage, 2)
            },
            "execution_quality": "CONSISTENT" if abs(paper_win_rate - bt_win_rate) < 15.0 else "DIVERGENT"
        }
