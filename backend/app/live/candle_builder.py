import datetime
from typing import Dict, Any, List, Optional
from app.live.data_types import LiveTick, LiveCandle

class LiveCandleBuilder:
    """
    Constructs 1-minute, 5-minute, and 15-minute OHLCV candles in real time from live tick streams.
    Prevents look-ahead bias and freezes historical bars upon closure.
    """

    def __init__(self):
        # Symbol -> Timeframe -> In-progress candle
        self._current_candles: Dict[str, Dict[str, LiveCandle]] = {}
        # Symbol -> Timeframe -> List of completed candles
        self._completed_candles: Dict[str, Dict[str, List[LiveCandle]]] = {}

    def ingest_tick(self, tick: LiveTick) -> Dict[str, Optional[LiveCandle]]:
        symbol = tick.symbol
        if symbol not in self._current_candles:
            self._current_candles[symbol] = {}
            self._completed_candles[symbol] = {"1m": [], "5m": [], "15m": []}

        closed_candles: Dict[str, Optional[LiveCandle]] = {"1m": None, "5m": None, "15m": None}

        for tf, minutes in [("1m", 1), ("5m", 5), ("15m", 15)]:
            closed = self._update_timeframe_candle(symbol, tf, minutes, tick)
            if closed:
                closed_candles[tf] = closed

        return closed_candles

    def _update_timeframe_candle(
        self,
        symbol: str,
        timeframe: str,
        minutes: int,
        tick: LiveTick
    ) -> Optional[LiveCandle]:
        tick_time = tick.timestamp
        # Truncate to bucket start
        minute_bucket = (tick_time.minute // minutes) * minutes
        bucket_start = tick_time.replace(minute=minute_bucket, second=0, microsecond=0)

        current = self._current_candles[symbol].get(timeframe)

        if current is None:
            # First candle
            self._current_candles[symbol][timeframe] = LiveCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=bucket_start,
                open=tick.ltp,
                high=tick.ltp,
                low=tick.ltp,
                close=tick.ltp,
                volume=tick.volume,
                is_closed=False
            )
            return None

        if bucket_start > current.timestamp:
            # Previous candle closed
            closed_candle = current.model_copy(update={"is_closed": True})
            self._completed_candles[symbol][timeframe].append(closed_candle)

            # Persist to Parquet columnar storage
            try:
                from app.data.parquet_storage import parquet_storage
                parquet_storage.save_candles([closed_candle], timeframe=timeframe)
            except Exception:
                pass

            # Start new candle
            self._current_candles[symbol][timeframe] = LiveCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=bucket_start,
                open=tick.ltp,
                high=tick.ltp,
                low=tick.ltp,
                close=tick.ltp,
                volume=tick.volume,
                is_closed=False
            )
            return closed_candle
        else:
            # Update in-progress candle
            current.high = max(current.high, tick.ltp)
            current.low = min(current.low, tick.ltp)
            current.close = tick.ltp
            current.volume += tick.volume
            return None

    def get_candles(self, symbol: str, timeframe: str = "5m", limit: int = 100) -> List[LiveCandle]:
        if symbol not in self._completed_candles or timeframe not in self._completed_candles[symbol]:
            return []
        completed = self._completed_candles[symbol][timeframe]
        return completed[-limit:]
