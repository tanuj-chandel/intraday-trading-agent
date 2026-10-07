from typing import List, Dict, Any

class ConcentrationRiskAnalyzer:
    """
    Evaluates whether strategy performance is driven by repeatable edge or concentrated in few outlier stocks/trades.
    """

    @classmethod
    def analyze_stock_concentration(
        cls,
        stock_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not stock_results:
            return {
                "top_1_stock_contribution_pct": 0.0,
                "top_3_stock_contribution_pct": 0.0,
                "top_5_stock_contribution_pct": 0.0,
                "stock_concentration_flag": "NO_DATA",
                "profit_concentration_note": "No multi-stock data available."
            }

        # Filter profitable stocks
        winning_stocks = [s for s in stock_results if s.get("net_pnl", 0) > 0]
        total_winning_pnl = sum(s.get("net_pnl", 0) for s in winning_stocks)

        if total_winning_pnl == 0:
            return {
                "top_1_stock_contribution_pct": 0.0,
                "top_3_stock_contribution_pct": 0.0,
                "top_5_stock_contribution_pct": 0.0,
                "stock_concentration_flag": "NO_PROFITABLE_STOCKS",
                "profit_concentration_note": "Strategy produced no net winning stocks."
            }

        sorted_stocks = sorted(winning_stocks, key=lambda x: x.get("net_pnl", 0), reverse=True)
        top1_pnl = sorted_stocks[0]["net_pnl"] if len(sorted_stocks) >= 1 else 0.0
        top3_pnl = sum(s["net_pnl"] for s in sorted_stocks[:3])
        top5_pnl = sum(s["net_pnl"] for s in sorted_stocks[:5])

        top1_pct = round((top1_pnl / total_winning_pnl) * 100.0, 1)
        top3_pct = round((top3_pnl / total_winning_pnl) * 100.0, 1)
        top5_pct = round((top5_pnl / total_winning_pnl) * 100.0, 1)

        is_high_risk = top3_pct > 70.0 or top1_pct > 50.0

        return {
            "top_1_stock_contribution_pct": top1_pct,
            "top_3_stock_contribution_pct": top3_pct,
            "top_5_stock_contribution_pct": top5_pct,
            "stock_concentration_flag": "HIGH_STOCK_CONCENTRATION_RISK" if is_high_risk else "BALANCED_DIVERSIFICATION",
            "profit_concentration_note": (
                f"Top 3 stocks contribute {top3_pct}% of total gross gains."
                if is_high_risk else "Gains are distributed reasonably across multiple universe constituents."
            )
        }

    @classmethod
    def analyze_trade_concentration(
        cls,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not trades:
            return {
                "top_1pct_trade_contribution_pct": 0.0,
                "top_5pct_trade_contribution_pct": 0.0,
                "top_10pct_trade_contribution_pct": 0.0,
                "trade_concentration_flag": "NO_TRADES"
            }

        winning_trades = [t for t in trades if t.get("net_pnl", 0) > 0]
        total_win_pnl = sum(t.get("net_pnl", 0) for t in winning_trades)

        if total_win_pnl == 0 or len(trades) < 10:
            return {
                "top_1pct_trade_contribution_pct": 0.0,
                "top_5pct_trade_contribution_pct": 0.0,
                "top_10pct_trade_contribution_pct": 0.0,
                "trade_concentration_flag": "INSUFFICIENT_TRADES_FOR_CONCENTRATION_AUDIT",
                "profit_concentration_note": f"Only {len(trades)} trades recorded (<10 threshold)."
            }

        sorted_wins = sorted(winning_trades, key=lambda x: x.get("net_pnl", 0), reverse=True)
        n = len(trades)

        k1 = max(1, int(n * 0.01))
        k5 = max(1, int(n * 0.05))
        k10 = max(1, int(n * 0.10))

        top1_pnl = sum(t["net_pnl"] for t in sorted_wins[:k1])
        top5_pnl = sum(t["net_pnl"] for t in sorted_wins[:k5])
        top10_pnl = sum(t["net_pnl"] for t in sorted_wins[:k10])

        top1_pct = round((top1_pnl / total_win_pnl) * 100.0, 1)
        top5_pct = round((top5_pnl / total_win_pnl) * 100.0, 1)
        top10_pct = round((top10_pnl / total_win_pnl) * 100.0, 1)

        is_high_risk = top5_pct > 60.0

        return {
            "top_1pct_trade_contribution_pct": top1_pct,
            "top_5pct_trade_contribution_pct": top5_pct,
            "top_10pct_trade_contribution_pct": top10_pct,
            "trade_concentration_flag": "PROFIT_CONCENTRATION_RISK" if is_high_risk else "HEALTHY_TRADE_DISTRIBUTION",
            "profit_concentration_note": (
                f"Top 5% of trades generate {top5_pct}% of total profits. Vulnerable to outlier luck."
                if is_high_risk else "Returns are evenly distributed across trading sequence."
            )
        }
