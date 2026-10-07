"""
Phase 8 — Alert Engine Tests
Tests for all alert types, severity levels, dedup cooldown,
active/resolved filtering, summary counts, and convenience methods.
"""
import datetime
import pytest
from app.live.alerter import Phase8AlertEngine, AlertType, AlertSeverity, Alert


def make_engine():
    engine = Phase8AlertEngine()
    engine._persist_to_db = lambda alert: None  # Don't touch DB in tests
    return engine


def test_fire_basic_alert():
    e = make_engine()
    alert = e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "Test disconnect")
    assert alert is not None
    assert alert.alert_type == AlertType.DATA_DISCONNECT
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.resolved is False


def test_fire_returns_none_when_deduped():
    e = make_engine()
    e.fire(AlertType.STALE_DATA, AlertSeverity.WARNING, "Stale", symbol="RELIANCE")
    # Second fire within cooldown should be suppressed
    result = e.fire(AlertType.STALE_DATA, AlertSeverity.WARNING, "Stale again", symbol="RELIANCE")
    assert result is None


def test_bypass_dedup():
    e = make_engine()
    e.fire(AlertType.KILL_SWITCH_ACTIVATED, AlertSeverity.CRITICAL, "KS activated", bypass_dedup=True)
    result = e.fire(AlertType.KILL_SWITCH_ACTIVATED, AlertSeverity.CRITICAL, "KS again", bypass_dedup=True)
    assert result is not None  # bypass_dedup=True skips cooldown


def test_resolve_alert():
    e = make_engine()
    alert = e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "Disconnect", bypass_dedup=True)
    e.resolve(alert.id)
    active = e.get_active_alerts()
    assert not any(a["id"] == alert.id for a in active)


def test_get_active_alerts_excludes_resolved():
    e = make_engine()
    a1 = e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "d1", bypass_dedup=True)
    a2 = e.fire(AlertType.HIGH_LATENCY, AlertSeverity.WARNING, "latency", bypass_dedup=True)
    e.resolve(a1.id)
    active = e.get_active_alerts()
    ids = [a["id"] for a in active]
    assert a1.id not in ids
    assert a2.id in ids


def test_get_active_by_severity():
    e = make_engine()
    e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "crit", bypass_dedup=True)
    e.fire(AlertType.HIGH_LATENCY, AlertSeverity.WARNING, "warn", bypass_dedup=True)
    crits = e.get_active_alerts(AlertSeverity.CRITICAL)
    assert all(a["severity"] == "CRITICAL" for a in crits)


def test_summary_counts():
    e = make_engine()
    e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "c1", bypass_dedup=True)
    e.fire(AlertType.HIGH_LATENCY, AlertSeverity.WARNING, "w1", bypass_dedup=True)
    e.fire(AlertType.SYSTEM_START, AlertSeverity.INFO, "i1", bypass_dedup=True)
    summary = e.get_summary()
    assert summary["active_alerts"] == 3
    assert summary["critical_active"] == 1
    assert summary["warning_active"] == 1
    assert summary["info_active"] == 1


def test_data_disconnect_convenience():
    e = make_engine()
    alert = e.data_disconnect("ZERODHA", "Timeout")
    assert alert is not None
    assert alert.alert_type == AlertType.DATA_DISCONNECT
    assert alert.severity == AlertSeverity.CRITICAL


def test_consecutive_losses_warning():
    e = make_engine()
    alert = e.consecutive_losses(3)
    assert alert.severity == AlertSeverity.WARNING


def test_consecutive_losses_critical():
    e = make_engine()
    alert = e.consecutive_losses(5)
    assert alert.severity == AlertSeverity.CRITICAL


def test_kill_switch_alert():
    e = make_engine()
    alert = e.kill_switch_activated(3, "Emergency stop")
    assert alert is not None
    assert alert.alert_type == AlertType.KILL_SWITCH_ACTIVATED
    assert alert.severity == AlertSeverity.CRITICAL


def test_missing_credentials_info():
    e = make_engine()
    alert = e.missing_credentials("ZERODHA")
    assert alert.severity == AlertSeverity.INFO


def test_high_latency_critical_above_1000ms():
    e = make_engine()
    alert = e.high_latency("ZERODHA", 1200.0)
    assert alert.severity == AlertSeverity.CRITICAL


def test_high_latency_warning_above_200ms():
    e = make_engine()
    alert = e.high_latency("ZERODHA", 500.0)
    assert alert.severity == AlertSeverity.WARNING


def test_alert_ring_buffer_max_size():
    """Ring buffer should not exceed MAX_ALERTS capacity."""
    e = make_engine()
    e.MAX_ALERTS = 10
    from collections import deque
    e._alerts = deque(maxlen=10)
    for i in range(15):
        e.fire(AlertType.SYSTEM_START, AlertSeverity.INFO, f"msg {i}", bypass_dedup=True)
    assert len(e._alerts) == 10  # Capped at 10


def test_all_alerts_endpoint():
    e = make_engine()
    e.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL, "test", bypass_dedup=True)
    all_alerts = e.get_all_alerts(limit=10)
    assert len(all_alerts) == 1
    assert all_alerts[0]["alert_type"] == "DATA_DISCONNECT"
