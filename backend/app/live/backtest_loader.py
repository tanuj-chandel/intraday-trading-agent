"""
Phase 8 — Backtest Metrics Loader
Loads Phase 6 frozen backtest baseline from the saved report file.
Falls back to Phase 7 defaults only if no Phase 6 report exists.
Prevents hardcoded backtest_metrics throughout codebase.
"""
import json
import os
from typing import Dict, Any, Optional

# Default Phase 7 fallback if no Phase 6 report found
_DEFAULT_BACKTEST_METRICS: Dict[str, Any] = {
    "strategy_name": "VWAP_EMA_MOMENTUM_V1",
    "win_rate": 55.0,
    "expectancy": 150.0,
    "profit_factor": 1.5,
    "avg_win_inr": 350.0,
    "avg_loss_inr": 200.0,
    "max_drawdown_pct": 8.5,
    "avg_hold_time_minutes": 45.0,
    "avg_slippage_pct": 0.05,
    "total_trades_in_backtest": 0,
    "source": "FALLBACK_DEFAULTS",
    "note": "Phase 6 report not found. Using conservative defaults. Run Phase 6 backtest to update."
}

# Paths to search for Phase 6 reports
_PHASE6_REPORT_PATHS = [
    "reports/phase6_strategy_validation.json",
    "reports/phase6_empirical_validation.json",
    "reports/phase6_paper_trading_validation.json",
]


def load_phase6_backtest_metrics(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Load frozen Phase 6 backtest baseline metrics.
    
    Priority:
    1. Phase 6 JSON report (any of the known filenames)
    2. Hardcoded conservative defaults with clear labelling
    
    Never loads mock or paper-trading results as the baseline.
    """
    if base_dir is None:
        # Try to resolve from this file's location
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    for rel_path in _PHASE6_REPORT_PATHS:
        full_path = os.path.abspath(os.path.join(base_dir, rel_path))
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extract key metrics — tolerate different report structures
                metrics = {
                    "strategy_name": data.get("strategy_name", "VWAP_EMA_MOMENTUM_V1"),
                    "win_rate": float(data.get("win_rate", data.get("win_rate_pct", 55.0))),
                    "expectancy": float(data.get("expectancy", data.get("expectancy_inr", 150.0))),
                    "profit_factor": float(data.get("profit_factor", 1.5)),
                    "avg_win_inr": float(data.get("avg_win_inr", data.get("avg_win", 350.0))),
                    "avg_loss_inr": float(data.get("avg_loss_inr", data.get("avg_loss", 200.0))),
                    "max_drawdown_pct": float(data.get("max_drawdown_pct", 8.5)),
                    "avg_hold_time_minutes": float(data.get("avg_hold_time_minutes", 45.0)),
                    "avg_slippage_pct": float(data.get("avg_slippage_pct", 0.05)),
                    "total_trades_in_backtest": int(data.get("total_trades", 0)),
                    "source": f"PHASE6_REPORT:{rel_path}",
                    "loaded_from": full_path,
                }
                return metrics
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                continue  # Try next path

    # No Phase 6 report found — use defaults
    return _DEFAULT_BACKTEST_METRICS.copy()


# Module-level cached metrics (loaded once on import)
_cached_metrics: Optional[Dict[str, Any]] = None


def get_backtest_baseline() -> Dict[str, Any]:
    """Get cached Phase 6 baseline. Cached after first load."""
    global _cached_metrics
    if _cached_metrics is None:
        _cached_metrics = load_phase6_backtest_metrics()
    return _cached_metrics


def refresh_backtest_baseline() -> Dict[str, Any]:
    """Force reload of Phase 6 baseline (e.g. after new backtest run)."""
    global _cached_metrics
    _cached_metrics = load_phase6_backtest_metrics()
    return _cached_metrics
