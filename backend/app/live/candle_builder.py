import datetime
from typing import Dict, Any, List, Optional
from app.live.data_types import LiveTick, LiveCandle


class LiveCandleBuilder:
    """
    Constructs 1-minute, 5-minute, and 15-minute OHLCV candles in real time from live tick streams.
    Prevents look-ahead bias and freezes historical bars upon closure.

    Patched:
      * seed_candles() lets a session preload historical completed bars so that
        EMA-21 / MACD(26) / RVOL-20 are meaningful from the first live bar.
      * tick.volume is expected to be a PER-TICK DELTA (the Angel adapter now
        provides this). Summing cumulative day volume here was a bug.
    """

    TIMEFRAMES = [("1m", 1), ("5m", 5), ("15m", 15)]

    def __init__(self):
        self._current_candles: Dict[str, Dict[str, LiveCandle]] = {}
        self._completed_candles: Dict[str, Dict[str, List[LiveCandle]]] = {}

    def _ensure_symbol(self, symbol: str) -> None:
        if symbol not in self._current_candles:
            self._current_candles[symbol] = {}
            self._completed_candles[symbol] = {tf: [] for tf, _ in self.TIMEFRAMES}

    # ------------------------------------------------------------ seeding

    def seed_candles(self, symbol: str, timeframe: str, bars: List[Dict[str, Any]]) -> int:
        """
        Preload completed historical bars (oldest -> newest). Each bar is a dict with
        timestamp (naive datetime), open, high, low, close, volume.
        Bars at or after an already-seen timestamp are ignored. Returns count added.
        """
        self._ensure_symbol(symbol)
        existing = self._completed_candles[symbol].setdefault(timeframe, [])
        last_ts = existing[-1].timestamp if existing else None
        added = 0
        for b in sorted(bars, key=lambda x: x["timestamp"]):
            ts = b["timestamp"]
            if last_ts is not None and ts <= last_ts:
                continue
            existing.append(LiveCandle(
                symbol=symbol, timeframe=timeframe, timestamp=ts,
                open=float(b["open"]), high=float(b["high"]), low=float(b["low"]),
                close=float(b["close"]), volume=int(b.get("volume", 0)), is_closed=True,
            ))
            last_ts = ts
            added += 1
        return added

    # ------------------------------------------------------------ live ticks

    def ingest_tick(self, tick: LiveTick) -> Dict[str, Optional[LiveCandle]]:
        self._ensure_symbol(tick.symbol)
        closed_candles: Dict[str, Optional[LiveCandle]] = {tf: None for tf, _ in self.TIMEFRAMES}
        for tf, minutes in self.TIMEFRAMES:
            closed = self._update_timeframe_candle(tick.symbol, tf, minutes, tick)
            if closed:
                closed_candles[tf] = closed
        return closed_candles

    def _update_timeframe_candle(
        self, symbol: str, timeframe: str, minutes: int, tick: LiveTick
    ) -> Optional[LiveCandle]:
        tick_time = tick.timestamp
        minute_bucket = (tick_time.minute // minutes) * minutes
        bucket_start = tick_time.replace(minute=minute_bucket, second=0, microsecond=0)

        current = self._current_candles[symbol].get(timeframe)

        if current is None:
            self._current_candles[symbol][timeframe] = self._new_candle(symbol, timeframe, bucket_start, tick)
            return None

        if bucket_start > current.timestamp:
            closed_candle = current.model_copy(update={"is_closed": True})
            # Don't append a live bar that duplicates/precedes a seeded historical bar.
            completed = self._completed_candles[symbol][timeframe]
            if not completed or closed_candle.timestamp > completed[-1].timestamp:
                completed.append(closed_candle)
                try:
                    from app.data.parquet_storage import parquet_storage
                    parquet_storage.save_candles([closed_candle], timeframe=timeframe)
                except Exception:
                    pass

            self._current_candles[symbol][timeframe] = self._new_candle(symbol, timeframe, bucket_start, tick)
            return closed_candle

        current.high = max(current.high, tick.ltp)
        current.low = min(current.low, tick.ltp)
        current.close = tick.ltp
        current.volume += max(0, int(tick.volume))
        return None

    @staticmethod
    def _new_candle(symbol: str, timeframe: str, bucket_start: datetime.datetime, tick: LiveTick) -> LiveCandle:
        return LiveCandle(
            symbol=symbol, timeframe=timeframe, timestamp=bucket_start,
            open=tick.ltp, high=tick.ltp, low=tick.ltp, close=tick.ltp,
            volume=max(0, int(tick.volume)), is_closed=False,
        )

    # ------------------------------------------------------------ access

    def get_candles(self, symbol: str, timeframe: str = "5m", limit: int = 100) -> List[LiveCandle]:
        if symbol not in self._completed_candles or timeframe not in self._completed_candles[symbol]:
            return []
        return self._completed_candles[symbol][timeframe][-limit:]

    def get_current_candle(self, symbol: str, timeframe: str = "5m") -> Optional[LiveCandle]:
        return self._current_candles.get(symbol, {}).get(timeframe)
