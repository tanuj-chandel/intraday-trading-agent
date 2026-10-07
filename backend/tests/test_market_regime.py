import pytest
import pandas as pd
import numpy as np
from app.market.regime import MarketRegimeEngine

def test_trending_up_regime():
    dates = pd.date_range(start="2026-01-01 09:15", periods=50, freq="5min")
    # Steady upward series
    prices = [100.0 + i * 1.5 for i in range(50)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.2 for p in prices],
        "high": [p + 0.5 for p in prices],
        "low": [p - 0.3 for p in prices],
        "close": prices,
        "volume": [5000 for _ in range(50)]
    })
    res = MarketRegimeEngine.classify_regime(df, prev_day_close=99.0)
    assert res["regime"] in ["TRENDING_UP", "GAP_UP", "HIGH_VOLATILITY"]
    assert res["trend_strength"] >= 0

def test_gap_up_regime():
    dates = pd.date_range(start="2026-01-01 09:15", periods=40, freq="5min")
    prices = [120.0 + i * 0.1 for i in range(40)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.2 for p in prices],
        "high": [p + 0.5 for p in prices],
        "low": [p - 0.3 for p in prices],
        "close": prices,
        "volume": [5000 for _ in range(40)]
    })
    # Previous day close was 100, open is 119.8 -> +19.8% gap
    res = MarketRegimeEngine.classify_regime(df, prev_day_close=100.0)
    assert res["regime"] == "GAP_UP"
    assert res["gap_pct"] > 0
