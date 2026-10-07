"""
Phase 6 Enhanced Walk-Forward & Out-of-Sample Cross Validation Engine.
Performs rigorous Walk-Forward analysis on historical data with:
- Dynamic liquidity-tiered slippage matching live execution
- Realistic statutory Indian brokerage and tax deductions (STT, exchange, SEBI, GST, stamp duty)
- Out-of-sample (OOS) holdout validation
- Multi-window rolling walk-forward evaluation
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from app.backtest.engine import BacktestEngine, BacktestConfig
from app.backtest.cost_calculator import TransactionCostConfig
from app.execution.slippage_model import DynamicSlippageModel

class WalkForwardAnalyzer:
    """
    Evaluates strategy parameter robustness and prevents overfitting
    using out-of-sample testing and walk-forward efficiency metrics.
    """

    @classmethod
    def _prepare_config(cls, symbol: str, config: Optional[BacktestConfig]) -> BacktestConfig:
        cfg = config or BacktestConfig()
        # Ensure slippage is derived from dynamic liquidity tier if default
        tier_slip = DynamicSlippageModel.get_slippage_pct(symbol)
        cfg.slippage_pct = tier_slip
        cfg.cost_config = TransactionCostConfig(slippage_pct=tier_slip)
        return cfg

    @classmethod
    def analyze(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        """
        Three-way split: Training (50%), Validation (25%), Out-of-Sample Test (25%).
        """
        config = cls._prepare_config(symbol, config)
        n = len(df)
        if n < 40:
            raise ValueError(f"Dataset insufficient for Walk-Forward split (need >= 40 candles, got {n})")

        train_end = int(n * 0.50)
        val_end = int(n * 0.75)

        df_train = df.iloc[:train_end].copy().reset_index(drop=True)
        df_val = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        df_oos = df.iloc[val_end:].copy().reset_index(drop=True)

        engine = BacktestEngine(config)
        res_train = engine.run(df_train, symbol)
        res_val = engine.run(df_val, symbol)
        res_oos = engine.run(df_oos, symbol)

        train_pf = max(0.1, res_train["profit_factor"])
        oos_pf = max(0.1, res_oos["profit_factor"])
        wfe_ratio = round(oos_pf / train_pf, 2)

        is_stable = wfe_ratio >= 0.70 and res_oos["net_pnl"] >= 0

        return {
            "symbol": symbol,
            "validation_type": "WALK_FORWARD_CROSS_VALIDATION",
            "slippage_model": f"DYNAMIC_TIER_{DynamicSlippageModel.get_liquidity_tier(symbol)} ({config.slippage_pct*100:.3f}%)",
            "cost_model": "INDIAN_STATUTORY_INTRA_DAY",
            "is_stable": is_stable,
            "walk_forward_efficiency_ratio": wfe_ratio,
            "training_period": {
                "candle_count": len(df_train),
                "net_pnl": res_train["net_pnl"],
                "return_pct": res_train["return_pct"],
                "win_rate": res_train["win_rate"],
                "profit_factor": res_train["profit_factor"],
                "total_trades": res_train["total_trades"],
                "max_drawdown_pct": res_train["max_drawdown_pct"]
            },
            "validation_period": {
                "candle_count": len(df_val),
                "net_pnl": res_val["net_pnl"],
                "return_pct": res_val["return_pct"],
                "win_rate": res_val["win_rate"],
                "profit_factor": res_val["profit_factor"],
                "total_trades": res_val["total_trades"],
                "max_drawdown_pct": res_val["max_drawdown_pct"]
            },
            "out_of_sample_period": {
                "candle_count": len(df_oos),
                "net_pnl": res_oos["net_pnl"],
                "return_pct": res_oos["return_pct"],
                "win_rate": res_oos["win_rate"],
                "profit_factor": res_oos["profit_factor"],
                "total_trades": res_oos["total_trades"],
                "max_drawdown_pct": res_oos["max_drawdown_pct"]
            },
            "verdict": (
                "Strategy displays robust out-of-sample stability."
                if is_stable
                else "Potential curve-fitting detected: Out-of-sample performance diverges from training."
            )
        }

    @classmethod
    def out_of_sample_split(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        train_pct: float = 0.70,
        config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        """
        Two-way In-Sample (e.g. 70%) vs Out-of-Sample (30%) split.
        """
        config = cls._prepare_config(symbol, config)
        n = len(df)
        if n < 30:
            raise ValueError(f"Dataset insufficient for OOS split (need >= 30 candles, got {n})")

        split_idx = int(n * train_pct)
        df_in = df.iloc[:split_idx].copy().reset_index(drop=True)
        df_out = df.iloc[split_idx:].copy().reset_index(drop=True)

        engine = BacktestEngine(config)
        res_in = engine.run(df_in, symbol)
        res_out = engine.run(df_out, symbol)

        in_pf = max(0.1, res_in["profit_factor"])
        out_pf = max(0.1, res_out["profit_factor"])
        wfe_ratio = round(out_pf / in_pf, 2)
        is_stable = wfe_ratio >= 0.65 and res_out["net_pnl"] >= 0

        return {
            "symbol": symbol,
            "validation_type": "IN_SAMPLE_OUT_OF_SAMPLE_SPLIT",
            "split_ratio": f"{int(train_pct*100)}/{int((1-train_pct)*100)}",
            "slippage_model": f"DYNAMIC_TIER_{DynamicSlippageModel.get_liquidity_tier(symbol)} ({config.slippage_pct*100:.3f}%)",
            "is_stable": is_stable,
            "walk_forward_efficiency_ratio": wfe_ratio,
            "in_sample": {
                "candles": len(df_in),
                "net_pnl": res_in["net_pnl"],
                "win_rate": res_in["win_rate"],
                "profit_factor": res_in["profit_factor"],
                "trades": res_in["total_trades"]
            },
            "out_of_sample": {
                "candles": len(df_out),
                "net_pnl": res_out["net_pnl"],
                "win_rate": res_out["win_rate"],
                "profit_factor": res_out["profit_factor"],
                "trades": res_out["total_trades"]
            }
        }

    @classmethod
    def rolling_walk_forward(
        cls,
        df: pd.DataFrame,
        symbol: str = "RELIANCE",
        windows: int = 3,
        train_ratio: float = 0.60,
        config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        """
        Multi-window rolling walk-forward test across consecutive chronological windows.
        """
        config = cls._prepare_config(symbol, config)
        n = len(df)
        if n < windows * 20:
            raise ValueError(f"Insufficient candles for {windows} rolling windows (need >= {windows*20}, got {n})")

        window_size = n // windows
        window_results: List[Dict[str, Any]] = []
        engine = BacktestEngine(config)

        for w in range(windows):
            start_i = w * window_size
            end_i = (w + 1) * window_size if w < windows - 1 else n
            sub_df = df.iloc[start_i:end_i].copy().reset_index(drop=True)
            
            sub_split = int(len(sub_df) * train_ratio)
            train_sub = sub_df.iloc[:sub_split].copy().reset_index(drop=True)
            test_sub = sub_df.iloc[sub_split:].copy().reset_index(drop=True)

            res_tr = engine.run(train_sub, symbol)
            res_te = engine.run(test_sub, symbol)

            w_wfe = round(max(0.1, res_te["profit_factor"]) / max(0.1, res_tr["profit_factor"]), 2)
            window_results.append({
                "window_index": w + 1,
                "train_candles": len(train_sub),
                "test_candles": len(test_sub),
                "train_pnl": res_tr["net_pnl"],
                "test_pnl": res_te["net_pnl"],
                "train_pf": res_tr["profit_factor"],
                "test_pf": res_te["profit_factor"],
                "wfe": w_wfe,
                "passed": res_te["net_pnl"] >= 0 and w_wfe >= 0.60
            })

        all_passed = all(wr["passed"] for wr in window_results)
        avg_wfe = round(sum(wr["wfe"] for wr in window_results) / len(window_results), 2)

        return {
            "symbol": symbol,
            "validation_type": "ROLLING_WALK_FORWARD",
            "total_windows": windows,
            "slippage_model": f"DYNAMIC_TIER_{DynamicSlippageModel.get_liquidity_tier(symbol)} ({config.slippage_pct*100:.3f}%)",
            "overall_robust": all_passed,
            "average_wfe": avg_wfe,
            "windows": window_results
        }
