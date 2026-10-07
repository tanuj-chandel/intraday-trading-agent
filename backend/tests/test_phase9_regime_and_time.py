"""
Phase 9 — Regime and Time-of-Day Attribution Tests

Tests performance attribution across the 9 market regimes and 5 intraday time slots.
"""
import datetime
import pytest
from app.phase9.regime_analyzer import Phase9RegimeAnalyzer
from app.phase9.time_of_day_analyzer import Phase9TimeOfDayAnalyzer


def test_regime_attribution_9_regimes():
    """Verify all 9 regimes are represented in analysis."""
    trades = [
        {"market_regime": "TRENDING_UP", "net_pnl": 300.0, "gross_pnl": 350.0, "holding_minutes": 35.0},
        {"market_regime": "TRENDING_UP", "net_pnl": 200.0, "gross_pnl": 250.0, "holding_minutes": 40.0},
        {"market_regime": "TRENDING_DOWN", "net_pnl": 150.0, "gross_pnl": 200.0, "holding_minutes": 30.0},
        {"market_regime": "RANGE_BOUND", "net_pnl": -100.0, "gross_pnl": -50.0, "holding_minutes": 25.0},
        {"market_regime": "HIGH_VOLATILITY", "net_pnl": 400.0, "gross_pnl": 450.0, "holding_minutes": 15.0},
    ]

    res = Phase9RegimeAnalyzer.analyze(trades)
    assert res["total_trades_analyzed"] == 5
    assert len(res["regimes"]) >= 9

    # TRENDING_UP has 2 trades, 100% win rate
    tu = res["regimes"]["TRENDING_UP"]
    assert tu["trade_count"] == 2
    assert tu["win_rate_pct"] == 100.0
    assert tu["net_pnl"] == 500.0

    # Best regime should be identified
    assert res["best_regime"] in ("TRENDING_UP", "HIGH_VOLATILITY")


def test_time_of_day_attribution_5_slots():
    """Verify all 5 intraday time slots are analyzed."""
    trades = [
        {"time_of_day_bucket": "09:15–10:00", "net_pnl": 200.0, "entry_slippage": 5.0, "exit_slippage": 5.0},
        {"time_of_day_bucket": "10:00–11:30", "net_pnl": 350.0, "entry_slippage": 3.0, "exit_slippage": 3.0},
        {"time_of_day_bucket": "11:30–13:30", "net_pnl": -80.0, "entry_slippage": 2.0, "exit_slippage": 2.0},
        {"time_of_day_bucket": "13:30–14:30", "net_pnl": 150.0, "entry_slippage": 4.0, "exit_slippage": 4.0},
        {"time_of_day_bucket": "14:30–15:15", "net_pnl": -50.0, "entry_slippage": 6.0, "exit_slippage": 6.0},
    ]

    res = Phase9TimeOfDayAnalyzer.analyze(trades)
    assert res["total_trades_analyzed"] == 5
    assert len(res["time_slots"]) == 5

    morning = res["time_slots"]["10:00–11:30"]
    assert morning["trade_count"] == 1
    assert morning["net_pnl"] == 350.0
    assert morning["win_rate_pct"] == 100.0

    assert res["best_time_slot"] == "10:00–11:30"
