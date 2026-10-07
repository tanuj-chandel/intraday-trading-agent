import datetime
import pytest
from app.live.streamer import LiveTickStreamer
from app.live.data_types import LiveTick

def test_live_streamer_connection_and_tick_ingestion():
    streamer = LiveTickStreamer()
    streamer.connect(provider="ZERODHA_KITE", is_mock=True)

    assert streamer.is_connected is True
    assert streamer.provider_name == "ZERODHA_KITE"

    tick = LiveTick(
        symbol="RELIANCE",
        ltp=2950.0,
        open=2940.0,
        high=2960.0,
        low=2935.0,
        close=2950.0,
        volume=5000,
        bid=2949.5,
        ask=2950.5,
        spread=1.0,
        timestamp=datetime.datetime.now()
    )

    res = streamer.ingest_tick(tick)
    assert res["symbol"] == "RELIANCE"
    assert res["ltp"] == 2950.0
    assert "RELIANCE" in streamer.latest_ticks
