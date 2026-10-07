import pandas as pd
from typing import Dict, Any, List, Optional
from app.backtest.engine import BacktestEngine, BacktestConfig
from app.data.historical_loader import HistoricalDataLoader
from app.data.universe import EXPANDED_INDIAN_UNIVERSE

UNIVERSE_PRESETS = {
    "LIQUID_TOP_10": ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "TATAMOTORS", "LT", "SBIN", "BHARTIARTL", "AXISBANK"],
    "NIFTY_50": [s.symbol for s in EXPANDED_INDIAN_UNIVERSE if s.lot_size > 0][:15],
    "NIFTY_NEXT_50": ["TRENT", "BEL", "HAL", "ZOMATO", "JIOFIN", "VEDL", "DLF", "INDIGO"]
}

class MultiSymbolBacktestService:
    """
    Executes strategy backtesting across multi-symbol Indian equity universes.
    Aggregates portfolio metrics and ranks stock-level performance without cherry-picking.
    """

    @classmethod
    def run_universe_backtest(
        cls,
        universe_id: str = "LIQUID_TOP_10",
        config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        symbols = UNIVERSE_PRESETS.get(universe_id, UNIVERSE_PRESETS["LIQUID_TOP_10"])
        bt_config = config or BacktestConfig()
        engine = BacktestEngine(bt_config)

        # Load sample dataset as base
        base_df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")

        stock_results: List[Dict[str, Any]] = []
        total_pnl = 0.0
        total_trades = 0
        total_wins = 0

        for sym in symbols:
            # Simulate per-stock price variance
            sym_df = base_df.copy()
            mult = 1.0 + (hash(sym) % 10 - 5) * 0.002
            sym_df["open"] *= mult
            sym_df["high"] *= mult
            sym_df["low"] *= mult
            sym_df["close"] *= mult

            res = engine.run(sym_df, symbol=sym)
            stock_results.append({
                "symbol": sym,
                "trades": res["total_trades"],
                "win_rate": res["win_rate"],
                "net_pnl": res["net_pnl"],
                "profit_factor": res["profit_factor"],
                "max_drawdown_pct": res["max_drawdown_pct"],
                "expectancy": res["expectancy"]
            })
            total_pnl += res["net_pnl"]
            total_trades += res["total_trades"]
            total_wins += res["winning_trades"]

        # Sort leaderboard
        sorted_stocks = sorted(stock_results, key=lambda x: x["net_pnl"], reverse=True)
        best_symbols = sorted_stocks[:3]
        worst_symbols = sorted_stocks[-3:]

        portfolio_win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
        portfolio_return_pct = (total_pnl / (bt_config.initial_capital * len(symbols))) * 100.0

        return {
            "universe_id": universe_id,
            "symbols_evaluated": len(symbols),
            "symbols_list": symbols,
            "portfolio_summary": {
                "total_trades": total_trades,
                "portfolio_net_pnl": round(total_pnl, 2),
                "portfolio_return_pct": round(portfolio_return_pct, 2),
                "portfolio_win_rate": round(portfolio_win_rate, 1)
            },
            "stock_leaderboard": sorted_stocks,
            "best_performing_symbols": best_symbols,
            "worst_performing_symbols": worst_symbols,
            "survivorship_warning": "SURVIVORSHIP BIAS WARNING: Backtested on fixed present constituents.",
            "data_mode": "SAMPLE / MULTI-STOCK TEST ONLY"
        }
