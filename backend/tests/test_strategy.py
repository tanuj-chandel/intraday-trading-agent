import pytest
import pandas as pd
from app.strategies.vwap_ema_momentum import VWAPEMAMomentumStrategy

def test_vwap_ema_momentum_strategy():
    strategy = VWAPEMAMomentumStrategy()
    assert strategy.get_name() == "VWAP_EMA_Momentum_RVOL"
    
    dates = pd.date_range(start="2026-01-01 09:15", periods=50, freq="5min")
    prices = [1000.0 + i * 1.5 for i in range(50)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.5 for p in prices],
        "high": [p + 1.5 for p in prices],
        "low": [p - 0.5 for p in prices],
        "close": prices,
        "volume": [20000 for _ in range(50)]
    })
    
    sig = strategy.evaluate("RELIANCE", df, account_balance=100000.0, risk_per_trade_pct=0.01)
    if sig:
        assert sig.symbol == "RELIANCE"
        assert sig.direction in ["BUY", "SELL"]
        assert sig.entry_price > 0
        assert sig.stop_loss > 0
        assert sig.target_price > 0
        assert sig.quantity >= 1
        assert len(sig.explanation) > 0
