import pandas as pd
from typing import Dict, Any, List, Optional
from app.backtest.engine import BacktestEngine, BacktestConfig

class RollingWalkForwardService:
    """
    Rolling Walk-Forward Cross-Validation Engine.
    Steps sequentially across multiple time windows (W1, W2, W3...) to prevent curve-fitting.
    """

    @classmethod
    def run_rolling_walk_forward(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        windows_count: int = 3,
        config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        total_len = len(df)
        window_size = total_len // windows_count
        bt_config = config or BacktestConfig()
        engine = BacktestEngine(bt_config)

        windows_results: List[Dict[str, Any]] = []
        train_pfs = []
        oos_pfs = []

        for w_idx in range(windows_count):
            start_idx = w_idx * window_size
            end_idx = min(total_len, (w_idx + 1) * window_size)
            w_df = df.iloc[start_idx:end_idx].reset_index(drop=True)

            # Split within window: 60% Train, 20% Val, 20% OOS
            w_len = len(w_df)
            train_cut = int(w_len * 0.6)
            val_cut = int(w_len * 0.8)

            train_slice = w_df.iloc[:train_cut]
            val_slice = w_df.iloc[train_cut:val_cut]
            oos_slice = w_df.iloc[val_cut:]

            train_res = engine.run(train_slice, symbol) if len(train_slice) >= 10 else {"profit_factor": 1.0, "return_pct": 0.0, "total_trades": 0, "max_drawdown_pct": 0.0}
            val_res = engine.run(val_slice, symbol) if len(val_slice) >= 5 else {"profit_factor": 1.0, "return_pct": 0.0, "total_trades": 0, "max_drawdown_pct": 0.0}
            oos_res = engine.run(oos_slice, symbol) if len(oos_slice) >= 5 else {"profit_factor": 1.0, "return_pct": 0.0, "total_trades": 0, "max_drawdown_pct": 0.0}

            train_pfs.append(train_res.get("profit_factor", 1.0))
            oos_pfs.append(oos_res.get("profit_factor", 1.0))

            windows_results.append({
                "window": f"Window #{w_idx + 1}",
                "train_period": {"trades": train_res.get("total_trades", 0), "profit_factor": train_res.get("profit_factor", 1.0), "return_pct": train_res.get("return_pct", 0.0)},
                "validation_period": {"trades": val_res.get("total_trades", 0), "profit_factor": val_res.get("profit_factor", 1.0), "return_pct": val_res.get("return_pct", 0.0)},
                "oos_period": {"trades": oos_res.get("total_trades", 0), "profit_factor": oos_res.get("profit_factor", 1.0), "return_pct": oos_res.get("return_pct", 0.0)},
                "is_stable": oos_res.get("profit_factor", 1.0) >= 0.8
            })

        avg_train_pf = sum(train_pfs) / len(train_pfs) if train_pfs else 1.0
        avg_oos_pf = sum(oos_pfs) / len(oos_pfs) if oos_pfs else 1.0
        wfe_ratio = round(avg_oos_pf / avg_train_pf, 2) if avg_train_pf > 0 else 1.0

        return {
            "symbol": symbol,
            "total_windows": windows_count,
            "rolling_windows": windows_results,
            "aggregate_wfe_ratio": wfe_ratio,
            "overall_stability": "STABLE" if wfe_ratio >= 0.70 else "DEGRADED_OVERFITTING_WARNING",
            "data_source_mode": "SAMPLE / ROLLING WALK-FORWARD SIMULATION"
        }
