"""
Phase 9 — Symbol Concentration Risk Engine

Evaluates whether paper trading returns are broadly distributed across the universe
or heavily reliant on single-stock anomalies.
Flags HIGH_CONCENTRATION_RISK when Top 1 > 50% or Top 3 > 80% of gross profits.
"""
from typing import Dict, Any, List


class Phase9SymbolConcentrationEngine:
    """
    Evaluates concentration across active symbols.
    """

    @classmethod
    def analyze(cls, paper_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(paper_trades)
        if n == 0:
            return {
                "total_trades": 0,
                "active_symbols_count": 0,
                "symbols": [],
                "top1_contribution_pct": 0.0,
                "top3_contribution_pct": 0.0,
                "top5_contribution_pct": 0.0,
                "concentration_risk": "LOW",
                "disclaimer": "PAPER TRADING ONLY."
            }

        sym_stats: Dict[str, Dict[str, Any]] = {}
        total_gross_pnl = sum(max(0.0, t.get("gross_pnl", 0.0)) for t in paper_trades)
        if total_gross_pnl <= 0:
            total_gross_pnl = sum(abs(t.get("net_pnl", 0.0)) for t in paper_trades) or 1.0

        for t in paper_trades:
            sym = t.get("symbol", "UNKNOWN")
            if sym not in sym_stats:
                sym_stats[sym] = {
                    "symbol": sym,
                    "trade_count": 0,
                    "gross_pnl": 0.0,
                    "net_pnl": 0.0,
                    "wins": 0,
                    "losses": 0,
                }
            s = sym_stats[sym]
            s["trade_count"] += 1
            s["gross_pnl"] += t.get("gross_pnl", 0.0)
            s["net_pnl"] += t.get("net_pnl", 0.0)
            if t.get("net_pnl", 0.0) > 0:
                s["wins"] += 1
            else:
                s["losses"] += 1

        # Calculate contributions and sort by net_pnl
        sorted_syms = sorted(sym_stats.values(), key=lambda x: x["net_pnl"], reverse=True)

        for s in sorted_syms:
            s["win_rate_pct"] = round((s["wins"] / s["trade_count"] * 100.0) if s["trade_count"] > 0 else 0.0, 1)
            s["contribution_pct"] = round(max(0.0, s["net_pnl"]) / total_gross_pnl * 100.0, 1)
            s["net_pnl"] = round(s["net_pnl"], 2)
            s["gross_pnl"] = round(s["gross_pnl"], 2)

        top1 = sorted_syms[0]["contribution_pct"] if len(sorted_syms) >= 1 else 0.0
        top3 = sum(s["contribution_pct"] for s in sorted_syms[:3])
        top5 = sum(s["contribution_pct"] for s in sorted_syms[:5])

        # Flag determination
        if top1 > 50.0:
            risk = "HIGH_CONCENTRATION_RISK"
            warning = f"High concentration risk: Top symbol ({sorted_syms[0]['symbol']}) contributes {top1}% of total profit."
        elif top3 > 80.0:
            risk = "HIGH_CONCENTRATION_RISK"
            warning = f"High concentration risk: Top 3 symbols contribute {top3}% of total profit."
        elif top1 > 35.0 or top3 > 65.0:
            risk = "MODERATE_CONCENTRATION_RISK"
            warning = f"Moderate concentration: Top 3 symbols contribute {top3}% of profit."
        else:
            risk = "WELL_DIVERSIFIED"
            warning = "Profits and trades are distributed across the monitored universe."

        return {
            "total_trades": n,
            "active_symbols_count": len(sorted_syms),
            "top1_contribution_pct": round(top1, 1),
            "top3_contribution_pct": round(top3, 1),
            "top5_contribution_pct": round(top5, 1),
            "concentration_risk": risk,
            "warning": warning,
            "symbols": sorted_syms,
            "disclaimer": "PAPER TRADING ONLY — Symbol performance reflects simulated execution."
        }
