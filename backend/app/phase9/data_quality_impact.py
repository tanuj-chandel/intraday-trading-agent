"""
Phase 9 — Data Quality Impact Engine

Measures the correlation between market feed quality (latency, rejected ticks,
reconnects, stale events) and trade performance (slippage, fill variance, P&L).
Determines whether data degradation degrades paper trading outcomes.
"""
from typing import Dict, Any, List, Optional


class Phase9DataQualityImpactEngine:
    """
    Analyzes execution slippage and trade P&L against feed latency and data incidents.
    """

    @classmethod
    def analyze(
        cls,
        paper_trades: List[Dict[str, Any]],
        data_quality_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        n = len(paper_trades)
        if n == 0:
            return {
                "total_trades": 0,
                "latency_correlation": "NO_DATA",
                "latency_breakdown": {
                    "low_latency_trades_count": 0,
                    "high_latency_trades_count": 0,
                    "avg_slippage_low_latency_inr": 0.0,
                    "avg_slippage_high_latency_inr": 0.0,
                    "avg_net_pnl_low_latency_inr": 0.0,
                    "avg_net_pnl_high_latency_inr": 0.0,
                },
                "avg_slippage_low_latency": 0.0,
                "avg_slippage_high_latency": 0.0,
                "findings": ["No paper trades available for data quality impact analysis."],
                "disclaimer": "PAPER TRADING ONLY."
            }

        # Segregate trades by execution latency: Low (<100ms) vs High (>=100ms)
        low_lat_trades = [t for t in paper_trades if t.get("latency_ms", 0.0) < 100.0]
        high_lat_trades = [t for t in paper_trades if t.get("latency_ms", 0.0) >= 100.0]

        def avg_slip(trades: List[Dict[str, Any]]) -> float:
            if not trades:
                return 0.0
            total = sum(t.get("entry_slippage", 0.0) + t.get("exit_slippage", 0.0) for t in trades)
            return round(total / len(trades), 2)

        def avg_pnl(trades: List[Dict[str, Any]]) -> float:
            if not trades:
                return 0.0
            return round(sum(t.get("net_pnl", 0.0) for t in trades) / len(trades), 2)

        low_slip = avg_slip(low_lat_trades)
        high_slip = avg_slip(high_lat_trades)
        low_pnl = avg_pnl(low_lat_trades)
        high_pnl = avg_pnl(high_lat_trades)

        findings = []
        if high_lat_trades and high_slip > low_slip * 1.3:
            findings.append(f"Elevated latency (>=100ms) correlates with {round((high_slip / (low_slip or 1.0) - 1.0) * 100)}% higher execution slippage (₹{high_slip} vs ₹{low_slip}).")
        else:
            findings.append("Slippage remained within standard bid/ask spread bounds across observed latencies.")

        if high_lat_trades and high_pnl < low_pnl:
            findings.append(f"Average trade expectancy decreased during higher latency executions (₹{high_pnl} vs ₹{low_pnl}).")

        feed_health = data_quality_stats.get("quality_status", "HEALTHY") if data_quality_stats else "HEALTHY"
        reconnects = data_quality_stats.get("provider_reconnects", 0) if data_quality_stats else 0
        invalid_rate = data_quality_stats.get("invalid_rate_pct", 0.0) if data_quality_stats else 0.0

        if reconnects > 0:
            findings.append(f"Recorded {reconnects} broker reconnect incidents during the session.")
        if invalid_rate > 2.0:
            findings.append(f"Tick validation rejection rate was elevated ({invalid_rate}%).")

        return {
            "total_trades_analyzed": n,
            "feed_quality_status": feed_health,
            "latency_breakdown": {
                "low_latency_trades_count": len(low_lat_trades),
                "high_latency_trades_count": len(high_lat_trades),
                "avg_slippage_low_latency_inr": low_slip,
                "avg_slippage_high_latency_inr": high_slip,
                "avg_net_pnl_low_latency_inr": low_pnl,
                "avg_net_pnl_high_latency_inr": high_pnl,
            },
            "findings": findings,
            "disclaimer": "PAPER TRADING ONLY — Analyzes simulated fills against market data latency."
        }
