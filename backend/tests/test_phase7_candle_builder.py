import datetime
import pytest
from app.live.candle_builder import LiveCandleBuilder
from app.live.data_types import LiveTick

def test_candle_builder_aggregation_and_closure():
    builder = LiveCandleBuilder()
    base_time = datetime.datetime(2026, 8, 28, 9, 15, 0)

    # 1. First tick in 09:15 bucket
    t1 = LiveTick(
        symbol="RELIANCE", ltp=2900.0, open=2900.0, high=2900.0, low=2900.0, close=2900.0,
        volume=100, bid=2899.5, ask=2900.5, spread=1.0, timestamp=base_time
    )
    closed = builder.ingest_tick(t1)
    assert closed["1m"] is None

    # 2. Second tick in same 1m bucket with higher price
    t2 = LiveTick(
        symbol="RELIANCE", ltp=2910.0, open=2900.0, high=2910.0, low=2900.0, close=2910.0,
        volume=200, bid=2909.5, ask=2910.5, spread=1.0, timestamp=base_time + datetime.timedelta(seconds=30)
    )
    builder.ingest_tick(t2)

    # 3. Third tick in 09:16 bucket -> closes 09:15 1m candle!
    t3 = LiveTick(
        symbol="RELIANCE", ltp=2905.0, open=2905.0, high=2905.0, low=2905.0, close=2905.0,
        volume=150, bid=2904.5, ask=2905.5, spread=1.0, timestamp=base_time + datetime.timedelta(minutes=1, seconds=5)
    )
    closed_res = builder.ingest_tick(t3)
    assert closed_res["1m"] is not None
    assert closed_res["1m"].open == 2900.0
    assert closed_res["1m"].high == 2910.0
    assert closed_res["1m"].close == 2910.0
    assert closed_res["1m"].is_closed is True
