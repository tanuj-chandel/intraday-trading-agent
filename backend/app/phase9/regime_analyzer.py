"""
Phase 9 — Market Regime Attribution Analyzer

Segment paper trade performance across 9 distinct Indian market regimes:
TRENDING_UP, TRENDING_DOWN, RANGE_BOUND, HIGH_VOLATILITY, LOW_VOLATILITY,
GAP_UP, GAP_DOWN, BREAKOUT, BREAKDOWN.

Strict rule: Purely observational evidence reporting. Never auto-disables regimes.
"""
from typing import Dict, Any, List


class Phase9RegimeAnalyzer:
    """
    Evaluates paper trading performance grouped by the market regime snapshot at signal time.
    """

    ALL_REGIMES = [
        "TRENDING_UP",
        "TRENDING_DOWN",
        "RANGE_BOUND",
        "HIGH_VOLATILITY",
        "LOW_VOLATILITY",
        "GAP_UP",
        "GAP_DOWN",
        "BREAKOUT",
        "BREAKDOWN",
    ]

    @classmethod
    def analyze(cls, paper_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Group trades by market regime and compute performance per regime.
        """
        regime_buckets: Dict[str, List[Dict[str, Any]]] = {r: [] for r in cls.ALL_REGIMES}
        regime_buckets["OTHER"] = []

        for t in paper_trades:
            r = t.get("market_regime", "OTHER")
            # Map legacy SIDEWAYS or BULLISH to Phase 9 regime set if needed
            if r == "SIDEWAYS":
                r = "RANGE_BOUND"
            elif r == "HIGH_VOL":
                r = "HIGH_VOLATILITY"
            elif r == "LOW_VOL":
                r = "LOW_VOLATILITY"
            elif r == "BULLISH":
                r = "TRENDING_UP"
            elif r == "BEARISH":
                r = "TRENDING_DOWN"

            if r in regime_buckets:
                regime_buckets[r].append(t)
            else:
                regime_buckets["OTHER"].append(t)

        results = {}
        for regime_name, trades in regime_buckets.items():
            count = len(trades)
            if count == 0:
                results[regime_name] = {
                    "trade_count": 0,
                    "win_rate_pct": 0.0,
                    "expectancy_inr": 0.0,
                    "gross_pnl": 0.0,
                    "net_pnl": 0.0,
                    "profit_factor": 0.0,
                    "max_drawdown": 0.0,
                    "avg_holding_minutes": 0.0,
                }
                continue

            pnls = [t.get("net_pnl", 0.0) for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]
            win_rate = (len(wins) / count * 100.0)

            avg_win = sum(wins) / len(wins) if wins else 0.0
            avg_loss = abs(sum(losses)) / len(losses) if losses else 0.0
            expectancy = (win_rate / 100.0 * avg_win) - ((1.0 - win_rate / 100.0) * avg_loss)

            gross_wins = sum(wins)
            gross_losses = abs(sum(losses))
            pf = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

            # Drawdown
            running = 0.0
            peak = 0.0
            max_dd = 0.0
            for p in pnls:
                running += p
                if running > peak:
                    peak = running
                dd = peak - running
                if dd > max_dd:
                    max_dd = dd

            avg_hold = sum(t.get("holding_minutes", 0.0) for t in trades) / count

            results[regime_name] = {
                "trade_count": count,
                "win_rate_pct": round(win_rate, 2),
                "expectancy_inr": round(expectancy, 2),
                "gross_pnl": round(sum(t.get("gross_pnl", 0.0) for t in trades), 2),
                "net_pnl": round(sum(pnls), 2),
                "profit_factor": round(pf, 2),
                "max_drawdown": round(max_dd, 2),
                "avg_holding_minutes": round(avg_hold, 1),
            }

        return {
            "total_trades_analyzed": len(paper_trades),
            "regimes": results,
            "best_regime": max(
                (r for r, d in results.items() if d["trade_count"] > 0),
                key=lambda r: results[r]["expectancy_inr"],
                default=None
            ),
            "worst_regime": min(
                (r for r, d in results.items() if d["trade_count"] > 0),
                key=lambda r: results[r]["expectancy_inr"],
                default=None
            ),
            "disclaimer": "PAPER TRADING ONLY — Regimes are observed without algorithmic tuning or auto-disabling."
        }
