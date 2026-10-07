from typing import Dict, Any, List
import pandas as pd
from app.backtest.engine import BacktestEngine, BacktestConfig

class StrategyComparisonService:
    """
    Compares multiple strategy variants across common performance criteria:
    Return %, Profit Factor, Expectancy, Win Rate, Max Drawdown %, and Sharpe Ratio.
    """

    @classmethod
    def compare(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        # Variant A: Standard VWAP + EMA 9/21
        cfg_a = BacktestConfig(
            strategy_id="VWAP_EMA_MOMENTUM_V1",
            initial_capital=initial_capital,
            strategy_params={"ema_fast": 9, "ema_slow": 21, "min_rvol": 1.15}
        )
        engine_a = BacktestEngine(cfg_a)
        res_a = engine_a.run(df, symbol)

        # Variant B: Aggressive Momentum (EMA 7/18, RVOL 1.0)
        cfg_b = BacktestConfig(
            strategy_id="VWAP_EMA_MOMENTUM_V1",
            initial_capital=initial_capital,
            strategy_params={"ema_fast": 7, "ema_slow": 18, "min_rvol": 1.0, "sl_multiplier": 1.2}
        )
        engine_b = BacktestEngine(cfg_b)
        res_b = engine_b.run(df, symbol)

        # Variant C: Conservative Trend (EMA 12/26, RVOL 1.3)
        cfg_c = BacktestConfig(
            strategy_id="VWAP_EMA_MOMENTUM_V1",
            initial_capital=initial_capital,
            strategy_params={"ema_fast": 12, "ema_slow": 26, "min_rvol": 1.3, "sl_multiplier": 1.8}
        )
        engine_c = BacktestEngine(cfg_c)
        res_c = engine_c.run(df, symbol)

        strategies = [
            {
                "name": "Standard (EMA 9/21, RVOL 1.15)",
                "net_pnl": res_a["net_pnl"],
                "return_pct": res_a["return_pct"],
                "profit_factor": res_a["profit_factor"],
                "win_rate": res_a["win_rate"],
                "total_trades": res_a["total_trades"],
                "max_drawdown_pct": res_a["max_drawdown_pct"],
                "sharpe_ratio": res_a["sharpe_ratio"]
            },
            {
                "name": "Aggressive (EMA 7/18, RVOL 1.0)",
                "net_pnl": res_b["net_pnl"],
                "return_pct": res_b["return_pct"],
                "profit_factor": res_b["profit_factor"],
                "win_rate": res_b["win_rate"],
                "total_trades": res_b["total_trades"],
                "max_drawdown_pct": res_b["max_drawdown_pct"],
                "sharpe_ratio": res_b["sharpe_ratio"]
            },
            {
                "name": "Conservative (EMA 12/26, RVOL 1.3)",
                "net_pnl": res_c["net_pnl"],
                "return_pct": res_c["return_pct"],
                "profit_factor": res_c["profit_factor"],
                "win_rate": res_c["win_rate"],
                "total_trades": res_c["total_trades"],
                "max_drawdown_pct": res_c["max_drawdown_pct"],
                "sharpe_ratio": res_c["sharpe_ratio"]
            }
        ]

        return {
            "symbol": symbol,
            "data_source_mode": "SAMPLE / SIMULATION BACKTEST ONLY",
            "strategies": strategies,
            "recommended_variant": "Standard (EMA 9/21, RVOL 1.15)"
        }
