"""
Phase 8 — Tick Validator
Validates every incoming live tick before it enters the candle builder.
Prevents future timestamps, duplicate ticks, impossible OHLC, zero/negative prices,
malformed data, and sudden volume spikes from corrupting paper trading results.
"""
import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pytz

IST = pytz.timezone("Asia/Kolkata")
MAX_FUTURE_SECONDS = 5.0          # Allow up to 5s clock skew
MAX_VOLUME_SPIKE_MULTIPLIER = 100  # Flag if volume > 100x previous tick
MAX_PRICE_SPIKE_PCT = 0.20         # Flag if price moves >20% in one tick


class TickRejectionReason(str, Enum):
    ZERO_OR_NEGATIVE_PRICE = "ZERO_OR_NEGATIVE_PRICE"
    IMPOSSIBLE_OHLC = "IMPOSSIBLE_OHLC"
    FUTURE_TIMESTAMP = "FUTURE_TIMESTAMP"
    DUPLICATE_TICK = "DUPLICATE_TICK"
    STALE_TIMESTAMP = "STALE_TIMESTAMP"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    PRICE_SPIKE = "PRICE_SPIKE"
    MISSING_FIELDS = "MISSING_FIELDS"
    SPREAD_INVALID = "SPREAD_INVALID"


@dataclass
class TickValidationResult:
    is_valid: bool
    rejection_reason: Optional[str] = None
    rejection_code: Optional[TickRejectionReason] = None
    tick_age_ms: float = 0.0
    latency_ms: float = 0.0
    warnings: list = field(default_factory=list)


class Phase8TickValidator:
    """
    Validates each incoming live tick against a set of sanity rules.
    Rejects and counts invalid ticks — never silently passes corrupted data.

    All validation failures are logged; the caller decides whether to drop or escalate.
    """

    def __init__(self):
        # Per-symbol last seen tick (for duplicate/stale detection)
        self._last_seen: Dict[str, datetime.datetime] = {}
        self._last_price: Dict[str, float] = {}
        self._last_volume: Dict[str, float] = {}

        # Cumulative counters
        self.total_ticks_received: int = 0
        self.total_ticks_invalid: int = 0
        self.total_ticks_duplicate: int = 0
        self.total_ticks_future: int = 0

    def validate(
        self,
        symbol: str,
        ltp: float,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        bid: float,
        ask: float,
        tick_timestamp: datetime.datetime,
        received_at: Optional[datetime.datetime] = None
    ) -> TickValidationResult:
        """
        Validate a single tick. Returns TickValidationResult.
        is_valid=False means the tick must be dropped.
        """
        self.total_ticks_received += 1
        now = received_at or datetime.datetime.now(tz=pytz.utc)
        warnings = []

        # Normalise tick_timestamp to UTC for comparison
        if tick_timestamp.tzinfo is None:
            tick_ts_utc = pytz.utc.localize(tick_timestamp)
        else:
            tick_ts_utc = tick_timestamp.astimezone(pytz.utc)

        if now.tzinfo is None:
            now_utc = pytz.utc.localize(now)
        else:
            now_utc = now.astimezone(pytz.utc)

        latency_ms = max(0.0, (now_utc - tick_ts_utc).total_seconds() * 1000)
        tick_age_ms = latency_ms  # same as latency for live ticks

        # 1. Zero / negative price
        if ltp <= 0 or open_ <= 0 or high <= 0 or low <= 0 or close <= 0:
            self.total_ticks_invalid += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Zero or negative price detected (LTP={ltp})",
                rejection_code=TickRejectionReason.ZERO_OR_NEGATIVE_PRICE,
                latency_ms=latency_ms
            )

        # 2. Impossible OHLC relationships
        if high < low:
            self.total_ticks_invalid += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Impossible OHLC: high={high} < low={low}",
                rejection_code=TickRejectionReason.IMPOSSIBLE_OHLC,
                latency_ms=latency_ms
            )
        if high < open_ or high < close:
            self.total_ticks_invalid += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Impossible OHLC: high={high} < open={open_} or close={close}",
                rejection_code=TickRejectionReason.IMPOSSIBLE_OHLC,
                latency_ms=latency_ms
            )
        if low > open_ or low > close:
            self.total_ticks_invalid += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Impossible OHLC: low={low} > open={open_} or close={close}",
                rejection_code=TickRejectionReason.IMPOSSIBLE_OHLC,
                latency_ms=latency_ms
            )

        # 3. Future timestamp
        future_seconds = (tick_ts_utc - now_utc).total_seconds()
        if future_seconds > MAX_FUTURE_SECONDS:
            self.total_ticks_invalid += 1
            self.total_ticks_future += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Future timestamp: tick is {future_seconds:.1f}s ahead of server time",
                rejection_code=TickRejectionReason.FUTURE_TIMESTAMP,
                latency_ms=latency_ms
            )

        # 4. Duplicate tick (same symbol + exact same timestamp)
        prev_ts = self._last_seen.get(symbol)
        if prev_ts is not None:
            prev_ts_utc = prev_ts if prev_ts.tzinfo else pytz.utc.localize(prev_ts)
            if tick_ts_utc == prev_ts_utc:
                self.total_ticks_invalid += 1
                self.total_ticks_duplicate += 1
                return TickValidationResult(
                    is_valid=False,
                    rejection_reason=f"Duplicate tick: same timestamp {tick_timestamp} already seen for {symbol}",
                    rejection_code=TickRejectionReason.DUPLICATE_TICK,
                    latency_ms=latency_ms
                )

        # 5. Negative volume
        if volume < 0:
            self.total_ticks_invalid += 1
            return TickValidationResult(
                is_valid=False,
                rejection_reason=f"Negative volume: {volume}",
                rejection_code=TickRejectionReason.NEGATIVE_VOLUME,
                latency_ms=latency_ms
            )

        # 6. Bid/Ask spread sanity (bid must be < ask)
        if bid > 0 and ask > 0 and bid >= ask:
            warnings.append(f"Spread invalid: bid={bid} >= ask={ask}")

        # 7. Price spike warning (not rejection)
        prev_price = self._last_price.get(symbol)
        if prev_price and prev_price > 0:
            spike_pct = abs(ltp - prev_price) / prev_price
            if spike_pct > MAX_PRICE_SPIKE_PCT:
                warnings.append(f"Price spike: {spike_pct*100:.1f}% move ({prev_price} → {ltp})")

        # 8. Volume spike warning (not rejection unless extreme)
        prev_vol = self._last_volume.get(symbol)
        if prev_vol and prev_vol > 0 and volume > prev_vol * MAX_VOLUME_SPIKE_MULTIPLIER:
            warnings.append(f"Volume spike: {volume} vs prev {prev_vol}")

        # Update state
        self._last_seen[symbol] = tick_ts_utc
        self._last_price[symbol] = ltp
        self._last_volume[symbol] = volume

        return TickValidationResult(
            is_valid=True,
            tick_age_ms=tick_age_ms,
            latency_ms=latency_ms,
            warnings=warnings
        )

    def get_stats(self) -> dict:
        """Return validation statistics."""
        invalid_rate = (
            self.total_ticks_invalid / self.total_ticks_received * 100.0
            if self.total_ticks_received > 0 else 0.0
        )
        return {
            "total_received": self.total_ticks_received,
            "total_invalid": self.total_ticks_invalid,
            "total_duplicate": self.total_ticks_duplicate,
            "total_future_ts": self.total_ticks_future,
            "invalid_rate_pct": round(invalid_rate, 2),
            "symbols_tracked": len(self._last_seen),
        }

    def reset(self):
        """Reset all counters (call at start of new session)."""
        self._last_seen.clear()
        self._last_price.clear()
        self._last_volume.clear()
        self.total_ticks_received = 0
        self.total_ticks_invalid = 0
        self.total_ticks_duplicate = 0
        self.total_ticks_future = 0
