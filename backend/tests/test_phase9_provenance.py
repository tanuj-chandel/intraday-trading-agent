"""
Phase 9 — Provenance & Mode Indicator Tests

Tests the 7-state data provenance classification, prominent UI indicators,
complete observation metadata decoration, and strict signal generation safety gate.
"""
import datetime
import pytest
from app.phase9.provenance import (
    Phase9ProvenanceEngine,
    Phase9ProvenanceState,
    Phase9UIMode,
)


def test_provenance_states_complete():
    """Verify all 7 provenance states are defined."""
    states = [s.value for s in Phase9ProvenanceState]
    expected = ["LIVE", "STALE", "MOCK", "SAMPLE", "MANUAL", "ERROR", "UNCONFIGURED"]
    for e in expected:
        assert e in states


def test_ui_indicator_mapping():
    """Verify UI indicator mapping matches prompt requirements."""
    live_ui = Phase9ProvenanceEngine.get_ui_indicator(Phase9ProvenanceState.LIVE)
    assert live_ui["mode"] == Phase9UIMode.LIVE_MARKET_DATA.value
    assert "🟢" in live_ui["badge"]

    stale_ui = Phase9ProvenanceEngine.get_ui_indicator(Phase9ProvenanceState.STALE)
    assert stale_ui["mode"] == Phase9UIMode.STALE_DATA.value
    assert "🟡" in stale_ui["badge"]

    mock_ui = Phase9ProvenanceEngine.get_ui_indicator(Phase9ProvenanceState.MOCK)
    assert mock_ui["mode"] == Phase9UIMode.MOCK_SIMULATION.value
    assert "⚪" in mock_ui["badge"]

    error_ui = Phase9ProvenanceEngine.get_ui_indicator(Phase9ProvenanceState.ERROR)
    assert error_ui["mode"] == Phase9UIMode.NO_LIVE_DATA.value
    assert "🔴" in error_ui["badge"]

    unconfig_ui = Phase9ProvenanceEngine.get_ui_indicator(Phase9ProvenanceState.UNCONFIGURED)
    assert unconfig_ui["mode"] == Phase9UIMode.NO_LIVE_DATA.value
    assert "🔴" in unconfig_ui["badge"]


def test_classify_feed_live():
    """Live state permits signals only when all conditions pass."""
    now = datetime.datetime.now()
    res = Phase9ProvenanceEngine.classify_feed(
        is_connected=True,
        is_mock=False,
        has_credentials=True,
        last_tick_time=now,
        last_tick_price=2980.0
    )
    assert res["state"] == Phase9ProvenanceState.LIVE.value
    assert res["can_generate_signals"] is True
    assert "🟢" in res["ui_indicator"]["badge"]


def test_classify_feed_stale_blocks_signals():
    """Stale tick (>30s) must block signal generation."""
    old_time = datetime.datetime.now() - datetime.timedelta(seconds=45)
    res = Phase9ProvenanceEngine.classify_feed(
        is_connected=True,
        is_mock=False,
        has_credentials=True,
        last_tick_time=old_time,
        last_tick_price=2980.0
    )
    assert res["state"] == Phase9ProvenanceState.STALE.value
    assert res["can_generate_signals"] is False
    assert "🟡" in res["ui_indicator"]["badge"]


def test_classify_feed_unconfigured_blocks_signals():
    """No credentials must return UNCONFIGURED and block signals."""
    res = Phase9ProvenanceEngine.classify_feed(
        is_connected=True,
        is_mock=False,
        has_credentials=False,
        last_tick_time=datetime.datetime.now(),
        last_tick_price=2980.0
    )
    assert res["state"] == Phase9ProvenanceState.UNCONFIGURED.value
    assert res["can_generate_signals"] is False
    assert "🔴" in res["ui_indicator"]["badge"]


def test_classify_feed_mock_blocks_signals():
    """Mock provider must block signals and indicate MOCK mode."""
    res = Phase9ProvenanceEngine.classify_feed(
        is_connected=True,
        is_mock=True,
        has_credentials=True,
        last_tick_time=datetime.datetime.now(),
        last_tick_price=2980.0
    )
    assert res["state"] == Phase9ProvenanceState.MOCK.value
    assert res["can_generate_signals"] is False
    assert "⚪" in res["ui_indicator"]["badge"]


def test_classify_feed_error_blocks_signals():
    """Provider error must transition to ERROR and block signals."""
    res = Phase9ProvenanceEngine.classify_feed(
        is_connected=True,
        is_mock=False,
        has_credentials=True,
        last_tick_time=datetime.datetime.now(),
        last_tick_price=2980.0,
        provider_error="HTTP 503 Service Unavailable"
    )
    assert res["state"] == Phase9ProvenanceState.ERROR.value
    assert res["can_generate_signals"] is False


def test_decorate_observation():
    """Observation record must retain complete metadata."""
    obs = Phase9ProvenanceEngine.decorate_observation(
        symbol="RELIANCE",
        price=2980.0,
        provider="ZERODHA_KITE",
        exchange="NSE",
        state=Phase9ProvenanceState.LIVE,
        latency_ms=45.2
    )
    assert obs["provider"] == "ZERODHA_KITE"
    assert obs["symbol"] == "RELIANCE"
    assert obs["exchange"] == "NSE"
    assert obs["timezone"] == "Asia/Kolkata"
    assert obs["provenance_state"] == "LIVE"
    assert obs["latency_ms"] == 45.2
    assert obs["validation_status"] == "VALID"
    assert obs["is_genuine_live"] is True
