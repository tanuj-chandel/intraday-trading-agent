"""
Phase 8 — Tick Validator Tests
Tests for all tick rejection cases: zero/negative prices, impossible OHLC,
future timestamps, duplicate ticks, negative volume, and valid ticks.
"""
import datetime
import pytest
import pytz

from app.live.tick_validator import Phase8TickValidator, TickRejectionReason

UTC = pytz.utc


def make_validator():
    return Phase8TickValidator()


def ts_now():
    return datetime.datetime.now(tz=UTC)


def ts_past(seconds: float = 2.0):
    return datetime.datetime.now(tz=UTC) - datetime.timedelta(seconds=seconds)


def ts_future(seconds: float = 10.0):
    return datetime.datetime.now(tz=UTC) + datetime.timedelta(seconds=seconds)


def valid_tick_kwargs(symbol="RELIANCE", ltp=2980.0, ts=None):
    return dict(
        symbol=symbol,
        ltp=ltp,
        open_=2970.0,
        high=2990.0,
        low=2965.0,
        close=ltp,
        volume=100000,
        bid=2979.0,
        ask=2981.0,
        tick_timestamp=ts or ts_past(),
    )


# ── Valid Tick ───────────────────────────────────────────────────────────────

def test_valid_tick_passes():
    v = make_validator()
    r = v.validate(**valid_tick_kwargs())
    assert r.is_valid is True
    assert r.rejection_code is None


def test_valid_tick_increments_counter():
    v = make_validator()
    v.validate(**valid_tick_kwargs())
    stats = v.get_stats()
    assert stats["total_received"] == 1
    assert stats["total_invalid"] == 0


# ── Zero / Negative Price ─────────────────────────────────────────────────────

def test_zero_ltp_rejected():
    v = make_validator()
    r = v.validate(**valid_tick_kwargs(ltp=0.0))
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.ZERO_OR_NEGATIVE_PRICE


def test_negative_ltp_rejected():
    v = make_validator()
    r = v.validate(**valid_tick_kwargs(ltp=-100.0))
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.ZERO_OR_NEGATIVE_PRICE


def test_zero_open_rejected():
    v = make_validator()
    kw = valid_tick_kwargs()
    kw["open_"] = 0.0
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.ZERO_OR_NEGATIVE_PRICE


# ── Impossible OHLC ──────────────────────────────────────────────────────────

def test_high_less_than_low_rejected():
    v = make_validator()
    kw = valid_tick_kwargs()
    kw["high"] = 2900.0   # less than low=2965
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.IMPOSSIBLE_OHLC


def test_high_less_than_open_rejected():
    v = make_validator()
    kw = valid_tick_kwargs()
    kw["high"] = 2960.0   # less than open=2970
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.IMPOSSIBLE_OHLC


def test_low_greater_than_open_rejected():
    v = make_validator()
    kw = valid_tick_kwargs()
    kw["low"] = 2980.0   # greater than open=2970 and close=2980 (borderline — high=2990 OK)
    kw["open_"] = 2975.0
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.IMPOSSIBLE_OHLC


# ── Future Timestamp ─────────────────────────────────────────────────────────

def test_future_timestamp_rejected():
    v = make_validator()
    kw = valid_tick_kwargs(ts=ts_future(10.0))
    kw["received_at"] = datetime.datetime.now(tz=UTC)
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.FUTURE_TIMESTAMP


def test_slightly_future_within_skew_accepted():
    """5s clock skew is allowed (MAX_FUTURE_SECONDS=5)."""
    v = make_validator()
    kw = valid_tick_kwargs(ts=ts_future(3.0))
    kw["received_at"] = datetime.datetime.now(tz=UTC)
    r = v.validate(**kw)
    assert r.is_valid is True  # Within 5s tolerance


# ── Duplicate Tick ───────────────────────────────────────────────────────────

def test_duplicate_tick_rejected():
    v = make_validator()
    fixed_ts = ts_past(2.0)
    v.validate(**valid_tick_kwargs(ts=fixed_ts))   # First tick accepted
    r = v.validate(**valid_tick_kwargs(ts=fixed_ts))  # Second same timestamp = duplicate
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.DUPLICATE_TICK


def test_different_timestamp_not_duplicate():
    v = make_validator()
    v.validate(**valid_tick_kwargs(ts=ts_past(3.0)))
    r = v.validate(**valid_tick_kwargs(ts=ts_past(2.0)))
    assert r.is_valid is True


# ── Negative Volume ──────────────────────────────────────────────────────────

def test_negative_volume_rejected():
    v = make_validator()
    kw = valid_tick_kwargs()
    kw["volume"] = -1
    r = v.validate(**kw)
    assert r.is_valid is False
    assert r.rejection_code == TickRejectionReason.NEGATIVE_VOLUME


# ── Stats ────────────────────────────────────────────────────────────────────

def test_stats_track_invalid_count():
    v = make_validator()
    v.validate(**valid_tick_kwargs(ltp=0.0))   # invalid
    v.validate(**valid_tick_kwargs())           # valid
    stats = v.get_stats()
    assert stats["total_received"] == 2
    assert stats["total_invalid"] == 1
    assert stats["invalid_rate_pct"] == 50.0


def test_reset_clears_state():
    v = make_validator()
    v.validate(**valid_tick_kwargs(ltp=0.0))
    v.reset()
    stats = v.get_stats()
    assert stats["total_received"] == 0
    assert stats["total_invalid"] == 0
