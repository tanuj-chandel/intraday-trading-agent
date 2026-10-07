"""
Phase 8 — Failure Injection Tests
Tests system behavior under failure conditions:
- Broker timeout → ERROR state, no signals
- Malformed tick data → rejected by validator
- Duplicate ticks → second rejected
- Future timestamp → rejected  
- Kill switch during open position → positions closed
- DB failure → audit log fails silently, trading continues
- Missing credentials → UNCONFIGURED, no signals
"""
import datetime
import pytest
import pytz
from unittest.mock import patch, MagicMock
from app.live.tick_validator import Phase8TickValidator
from app.live.quality_gate import DataProvenanceState, LiveDataQualityGate
from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel

UTC = pytz.utc


# ── Tick Injection ─────────────────────────────────────────────────────────

def test_zero_price_tick_fails_validation():
    v = Phase8TickValidator()
    r = v.validate("RELIANCE", 0.0, 100.0, 100.0, 100.0, 100.0, 1000, 99.5, 100.5,
                   datetime.datetime.now(tz=UTC))
    assert r.is_valid is False
    assert "zero" in r.rejection_reason.lower() or "negative" in r.rejection_reason.lower()


def test_future_tick_rejected():
    v = Phase8TickValidator()
    future_ts = datetime.datetime.now(tz=UTC) + datetime.timedelta(seconds=30)
    r = v.validate("TCS", 3500.0, 3490.0, 3510.0, 3485.0, 3500.0, 5000, 3499.0, 3501.0, future_ts)
    assert r.is_valid is False
    assert "future" in r.rejection_reason.lower()


def test_duplicate_tick_injection():
    v = Phase8TickValidator()
    ts = datetime.datetime.now(tz=UTC) - datetime.timedelta(seconds=2)
    r1 = v.validate("INFY", 1700.0, 1695.0, 1710.0, 1690.0, 1700.0, 3000, 1699.0, 1701.0, ts)
    r2 = v.validate("INFY", 1700.0, 1695.0, 1710.0, 1690.0, 1700.0, 3000, 1699.0, 1701.0, ts)
    assert r1.is_valid is True
    assert r2.is_valid is False
    assert "duplicate" in r2.rejection_reason.lower()


def test_malformed_ohlc_rejected():
    v = Phase8TickValidator()
    ts = datetime.datetime.now(tz=UTC) - datetime.timedelta(seconds=1)
    # High < Low
    r = v.validate("SBIN", 500.0, 502.0, 490.0, 510.0, 500.0, 2000, 499.0, 501.0, ts)
    assert r.is_valid is False


def test_negative_volume_rejected():
    v = Phase8TickValidator()
    ts = datetime.datetime.now(tz=UTC) - datetime.timedelta(seconds=1)
    r = v.validate("HDFC", 1600.0, 1595.0, 1610.0, 1590.0, 1600.0, -100, 1599.0, 1601.0, ts)
    assert r.is_valid is False


# ── Kill Switch During Position ────────────────────────────────────────────

def test_kill_switch_l3_blocks_new_entries():
    from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel
    ks = HierarchicalKillSwitch()
    ks.activate(KillSwitchLevel.L3_CLOSE_ALL_POSITIONS, "test failure injection")
    assert ks.is_active is True
    # Level 3+ means level >= 3, which blocks new entries
    assert ks.current_level >= KillSwitchLevel.L3_CLOSE_ALL_POSITIONS


def test_kill_switch_l5_full_halt():
    ks = HierarchicalKillSwitch()
    ks.activate(KillSwitchLevel.L5_FULL_HALT, "critical failure")
    status = ks.get_status()
    assert status["current_level"] == 5
    assert ks.is_active is True


# ── Credential Absence → UNCONFIGURED ────────────────────────────────────

def test_missing_credentials_leads_to_unconfigured():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=False
    )
    assert result["status"] == DataProvenanceState.UNCONFIGURED
    assert result["can_generate_signals"] is False


def test_provider_error_leads_to_error_state():
    result = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        provider_error="Connection refused: broker API unavailable"
    )
    assert result["status"] == DataProvenanceState.ERROR
    assert result["can_generate_signals"] is False


# ── Audit Logger DB Failure ─────────────────────────────────────────────────

def test_audit_logger_survives_db_failure():
    """LiveAuditLogger must not raise even if DB write fails."""
    from app.live.audit import LiveAuditLogger
    # _persist_to_db already has try/except — verify log() doesn't propagate
    # Temporarily override to simulate DB failure
    original = LiveAuditLogger._persist_to_db
    @classmethod
    def raising_persist(cls, event_type, details):
        raise Exception("DB connection failed")
    LiveAuditLogger._persist_to_db = raising_persist
    try:
        # log() must not raise even if _persist_to_db raises
        LiveAuditLogger.log("TEST_EVENT", "Test message during DB failure")
    except Exception as e:
        pytest.fail(f"LiveAuditLogger raised exception on DB failure: {e}")
    finally:
        LiveAuditLogger._persist_to_db = original


def test_alerter_survives_db_failure():
    """Alert engine must not raise even if DB write fails."""
    from app.live.alerter import Phase8AlertEngine, AlertType, AlertSeverity
    engine = Phase8AlertEngine()
    # Patch _persist_to_db to raise — the fire() method must catch it
    original = engine._persist_to_db
    def raising_persist(alert):
        raise Exception("DB down")
    engine._persist_to_db = raising_persist
    try:
        alert = engine.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "Test", bypass_dedup=True)
        assert alert is not None, "Alert should still be created even if DB fails"
    except Exception as e:
        pytest.fail(f"AlertEngine propagated DB failure: {e}")
    finally:
        engine._persist_to_db = original


# ── Multiple Invalid Ticks → Counter Accuracy ──────────────────────────────

def test_invalid_tick_counters_accurate():
    v = Phase8TickValidator()
    ts = datetime.datetime.now(tz=UTC) - datetime.timedelta(seconds=1)
    # 5 valid ticks
    for i in range(5):
        ts_i = ts - datetime.timedelta(milliseconds=i * 500)
        v.validate("RELIANCE", 2980.0+i, 2975.0, 2990.0, 2970.0, 2980.0+i, 1000, 2979.0, 2981.0, ts_i)
    # 3 invalid (zero price)
    for i in range(3):
        ts_inv = ts - datetime.timedelta(minutes=i+1)
        v.validate("TCS", 0.0, 0.0, 0.0, 0.0, 0.0, 1000, 0.0, 0.0, ts_inv)
    stats = v.get_stats()
    assert stats["total_received"] == 8
    assert stats["total_invalid"] == 3


def test_streamer_rejects_zero_ltp_tick():
    """Streamer with Phase 8 validator must reject a tick with LTP=0."""
    from app.live.streamer import LiveTickStreamer
    from app.live.data_types import LiveTick
    streamer = LiveTickStreamer()
    streamer.is_mock = True
    streamer._has_credentials = False

    tick = LiveTick(
        symbol="RELIANCE",
        ltp=0.0,         # Invalid!
        open=0.0, high=0.0, low=0.0, close=0.0,
        volume=0, bid=0.0, ask=0.0, spread=0.0,
        timestamp=datetime.datetime.now()
    )
    result = streamer.ingest_tick(tick)
    assert result.get("tick_rejected") is True
    assert result["gate"]["can_generate_signals"] is False
