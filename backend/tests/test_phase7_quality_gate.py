import datetime
import pytest
from app.live.quality_gate import LiveDataQualityGate, DataProvenanceState

def test_quality_gate_live_fresh_feed():
    """Fresh real feed should return LIVE state and permit signal generation."""
    now = datetime.datetime.now()
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=now,
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True
    )
    assert gate["can_generate_signals"] is True
    assert gate["status"] == DataProvenanceState.LIVE
    assert gate["trading_enabled"] is True

def test_quality_gate_stale_data_rejection():
    """Data older than MAX_FRESHNESS_SECONDS (30s) must return STALE state."""
    stale_time = datetime.datetime.now() - datetime.timedelta(seconds=45)
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=stale_time,
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.STALE
    assert "TRADING DISABLED" in gate["reason"]

def test_quality_gate_zero_silent_mock_fallback():
    """Mock provider must return MOCK state — never silently permit signals."""
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=True
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.MOCK
    assert "MOCK DATA CANNOT BE USED" in gate["reason"]

def test_quality_gate_disconnected():
    """Disconnected feed must return DISCONNECTED state."""
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=None,
        is_market_connected=False,
        is_mock_provider=False,
        has_credentials=True
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.DISCONNECTED

def test_quality_gate_unconfigured():
    """Missing credentials must return UNCONFIGURED state."""
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=False
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.UNCONFIGURED

def test_quality_gate_invalid_price():
    """Zero or negative price must return INVALID state."""
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        last_tick_price=0.0
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.INVALID

def test_quality_gate_provider_error():
    """Provider error string must return ERROR state."""
    gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True,
        provider_error="Connection timeout after 3s"
    )
    assert gate["can_generate_signals"] is False
    assert gate["status"] == DataProvenanceState.ERROR

def test_is_live_helper():
    """is_live() helper must return True only for LIVE state."""
    live_gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=False,
        has_credentials=True
    )
    mock_gate = LiveDataQualityGate.evaluate_live_feed(
        last_tick_time=datetime.datetime.now(),
        is_market_connected=True,
        is_mock_provider=True
    )
    assert LiveDataQualityGate.is_live(live_gate) is True
    assert LiveDataQualityGate.is_live(mock_gate) is False
