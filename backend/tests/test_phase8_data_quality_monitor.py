"""
Phase 8 — Data Quality Monitor Tests
Tests for tick quality tracking: latency, invalid rates, reconnect counting,
per-symbol stats, provider summary, and alert threshold detection.
"""
import time
import pytest
from app.live.data_quality_monitor import Phase8DataQualityMonitor


def test_record_valid_tick():
    m = Phase8DataQualityMonitor()
    m.record_tick("RELIANCE", latency_ms=15.0, is_valid=True)
    stats = m.get_symbol_stats("RELIANCE")
    assert stats is not None
    assert stats["tick_count"] == 1
    assert stats["invalid_tick_count"] == 0


def test_record_invalid_tick():
    m = Phase8DataQualityMonitor()
    m.record_tick("TCS", latency_ms=5.0, is_valid=False)
    stats = m.get_symbol_stats("TCS")
    assert stats["invalid_tick_count"] == 1
    assert stats["invalid_rate_pct"] == 100.0


def test_record_duplicate_tick():
    m = Phase8DataQualityMonitor()
    m.record_tick("INFY", latency_ms=10.0, is_valid=False, is_duplicate=True)
    stats = m.get_symbol_stats("INFY")
    assert stats["duplicate_count"] == 1


def test_latency_tracking():
    m = Phase8DataQualityMonitor()
    for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
        m.record_tick("RELIANCE", latency_ms=lat, is_valid=True)
    stats = m.get_symbol_stats("RELIANCE")
    assert stats["avg_latency_ms"] == 30.0
    assert stats["max_latency_ms"] == 50.0


def test_p95_latency():
    m = Phase8DataQualityMonitor()
    for i in range(100):
        m.record_tick("HDFC", latency_ms=float(i), is_valid=True)
    stats = m.get_symbol_stats("HDFC")
    assert stats["p95_latency_ms"] >= 94.0  # Should be around 95th percentile


def test_reconnect_tracking():
    m = Phase8DataQualityMonitor()
    # Record a tick first to create the symbol entry
    m.record_tick("RELIANCE", latency_ms=10.0, is_valid=True)
    m.record_reconnect("RELIANCE")
    m.record_reconnect("RELIANCE")
    # Provider-level reconnects are always tracked
    summary = m.get_provider_summary()
    assert summary["provider_reconnects"] == 2


def test_provider_summary_no_data():
    m = Phase8DataQualityMonitor()
    summary = m.get_provider_summary()
    assert summary["total_ticks"] == 0
    assert summary["quality_status"] == "HEALTHY"
    assert summary["symbols_tracked"] == 0


def test_provider_summary_with_data():
    m = Phase8DataQualityMonitor()
    m.record_tick("RELIANCE", latency_ms=50.0, is_valid=True)
    m.record_tick("TCS", latency_ms=30.0, is_valid=True)
    m.record_tick("TCS", latency_ms=20.0, is_valid=False)
    summary = m.get_provider_summary()
    assert summary["total_ticks"] == 3
    assert summary["total_invalid"] == 1
    assert summary["symbols_tracked"] == 2


def test_high_latency_generates_alert():
    m = Phase8DataQualityMonitor()
    for _ in range(5):
        m.record_tick("RELIANCE", latency_ms=300.0, is_valid=True)
    summary = m.get_provider_summary()
    # avg latency 300ms > LATENCY_WARN_MS (200ms)
    assert len(summary["quality_alerts"]) > 0
    assert any("latency" in a.lower() for a in summary["quality_alerts"])


def test_high_invalid_rate_generates_alert():
    m = Phase8DataQualityMonitor()
    for _ in range(4):
        m.record_tick("SBIN", latency_ms=10.0, is_valid=False)
    for _ in range(2):
        m.record_tick("SBIN", latency_ms=10.0, is_valid=True)
    summary = m.get_provider_summary()
    # invalid_rate = 4/6 = 66% > INVALID_RATE_WARN_PCT (5%)
    assert any("invalid" in a.lower() for a in summary["quality_alerts"])


def test_get_all_symbol_stats():
    m = Phase8DataQualityMonitor()
    m.record_tick("RELIANCE", latency_ms=10.0, is_valid=True)
    m.record_tick("TCS", latency_ms=20.0, is_valid=True)
    all_stats = m.get_all_symbol_stats()
    symbols = {s["symbol"] for s in all_stats}
    assert "RELIANCE" in symbols
    assert "TCS" in symbols


def test_reset_clears_all_stats():
    m = Phase8DataQualityMonitor()
    m.record_tick("RELIANCE", latency_ms=10.0, is_valid=True)
    m.reset()
    summary = m.get_provider_summary()
    assert summary["total_ticks"] == 0
    assert summary["symbols_tracked"] == 0
