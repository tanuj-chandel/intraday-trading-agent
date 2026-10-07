import datetime
import pytest
from app.live.signal_engine import LiveSignalEngine
from app.live.data_types import LiveCandle

def test_live_signal_engine_and_deduplication():
    engine = LiveSignalEngine()
    candles = [
        LiveCandle(symbol="RELIANCE", timeframe="5m", timestamp=datetime.datetime.now(), open=2900.0, high=2920.0, low=2895.0, close=2915.0, volume=10000)
        for _ in range(10)
    ]

    sig = engine.evaluate_symbol("RELIANCE", candles)
    if sig:
        assert sig.symbol == "RELIANCE"
        assert sig.status == "PENDING"
        assert sig.strategy_name == "VWAP_EMA_MOMENTUM_V1"

        # Deduplicator check: immediate second call for same symbol must return None!
        sig_dup = engine.evaluate_symbol("RELIANCE", candles)
        assert sig_dup is None
