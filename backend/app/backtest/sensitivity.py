import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.backtest.engine import BacktestEngine, BacktestConfig

class ParameterSensitivityAnalyzer:
    """
    Parameter Sensitivity & Overfitting Detection Matrix.
    Scans a grid of parameter combinations assessing performance continuity and variance.
    """

    @classmethod
    def analyze(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        base_config: BacktestConfig = None
    ) -> Dict[str, Any]:
        base_config = base_config or BacktestConfig()
        
        # Test ranges
        fast_emas = [7, 9, 12]
        slow_emas = [18, 21, 26]
        min_rvols = [1.0, 1.2, 1.5]

        grid_results = []
        pnl_values = []
        pf_values = []

        for fast in fast_emas:
            for slow in slow_emas:
                if fast >= slow:
                    continue
                for rvol in min_rvols:
                    test_params = base_config.strategy_params.copy()
                    test_params["ema_fast"] = fast
                    test_params["ema_slow"] = slow
                    test_params["min_rvol"] = rvol

                    cfg = BacktestConfig(
                        strategy_id=base_config.strategy_id,
                        initial_capital=base_config.initial_capital,
                        risk_per_trade_pct=base_config.risk_per_trade_pct,
                        strategy_params=test_params
                    )
                    engine = BacktestEngine(cfg)
                    res = engine.run(df, symbol)

                    pnl_values.append(res["net_pnl"])
                    pf_values.append(res["profit_factor"])

                    grid_results.append({
                        "ema_fast": fast,
                        "ema_slow": slow,
                        "min_rvol": rvol,
                        "total_trades": res["total_trades"],
                        "win_rate": res["win_rate"],
                        "profit_factor": res["profit_factor"],
                        "net_pnl": res["net_pnl"],
                        "max_drawdown_pct": res["max_drawdown_pct"]
                    })

        # Calculate stability coefficient of variation (CV)
        pnl_std = float(np.std(pnl_values)) if pnl_values else 0.0
        pnl_mean = float(np.mean(pnl_values)) if pnl_values else 1.0
        cv = round(abs(pnl_std / pnl_mean), 2) if pnl_mean != 0 else 1.0

        is_robust = cv < 0.65

        return {
            "symbol": symbol,
            "total_combinations_tested": len(grid_results),
            "data_source_mode": "SAMPLE / SIMULATION BACKTEST ONLY",
            "is_parameter_stable": is_robust,
            "coefficient_of_variation": cv,
            "stability_rating": "HIGH_STABILITY" if cv < 0.40 else ("MODERATE_STABILITY" if cv < 0.70 else "HIGH_SENSITIVITY_WARNING"),
            "best_combination": max(grid_results, key=lambda x: x["profit_factor"]) if grid_results else {},
            "median_profit_factor": round(float(np.median(pf_values)), 2) if pf_values else 1.0,
            "median_net_pnl": round(float(np.median(pnl_values)), 2) if pnl_values else 0.0,
            "grid_results": grid_results[:12],
            "overfitting_risk": "LOW" if is_robust else "ELEVATED (Fragile parameter plateau)"
        }
