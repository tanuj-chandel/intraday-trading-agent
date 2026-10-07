"""
Phase 8 — API Endpoints Tests
Tests for all new Phase 8 API endpoints.
Paper Trading ONLY. Tests do not require real broker credentials.
"""
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Phase 7 Endpoints Still Working ──────────────────────────────────────────

def test_live_status_returns_200():
    resp = client.get("/api/live/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trading_mode"] == "PAPER_TRADING_ONLY"
    assert data["real_order_execution"] == "DISABLED"


def test_live_data_health_returns_200():
    resp = client.get("/api/live/data-health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "is_connected" in data


def test_live_signals_returns_list():
    resp = client.get("/api/live/signals")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_live_positions_open():
    resp = client.get("/api/live/positions?status=OPEN")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_live_performance_returns_200():
    resp = client.get("/api/live/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "disclaimer" in data
    assert "PAPER TRADING" in data["disclaimer"]


def test_kill_switch_status_returns_200():
    resp = client.get("/api/live/kill-switch/status")
    assert resp.status_code == 200


def test_reality_gap_returns_200():
    resp = client.get("/api/live/reality-gap")
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert "disclaimer" in data
    assert data["disclaimer"] == "PAPER TRADING ONLY"


# ── Phase 8 New Endpoints ─────────────────────────────────────────────────────

def test_trade_journal_endpoint():
    resp = client.get("/api/live/trade-journal")
    assert resp.status_code == 200
    data = resp.json()
    assert "analytics" in data
    assert "entries" in data
    assert "disclaimer" in data
    assert "PAPER TRADING" in data["disclaimer"]


def test_execution_quality_endpoint():
    resp = client.get("/api/live/execution-quality")
    assert resp.status_code == 200
    data = resp.json()
    assert "disclaimer" in data


def test_validation_progress_endpoint():
    resp = client.get("/api/live/validation-progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "stage" in data
    assert "milestones" in data
    assert "paper_trades" in data
    assert data["disclaimer"] == "PAPER TRADING ONLY"
    assert "scientific_note" in data


def test_backtest_vs_paper_endpoint():
    resp = client.get("/api/live/backtest-vs-paper")
    assert resp.status_code == 200
    data = resp.json()
    assert "comparison" in data
    assert "frozen_strategy" in data
    assert data["frozen_strategy"] == "VWAP_EMA_MOMENTUM_V1"
    assert "disclaimer" in data


def test_regime_performance_endpoint():
    resp = client.get("/api/live/regime-performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "regime_performance" in data
    assert "disclaimer" in data


def test_alerts_endpoint():
    resp = client.get("/api/live/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "summary" in data
    assert isinstance(data["alerts"], list)


def test_data_quality_endpoint():
    resp = client.get("/api/live/data-quality")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_provenance" in data
    assert "disclaimer" in data


def test_concentration_endpoint():
    resp = client.get("/api/live/concentration")
    assert resp.status_code == 200
    data = resp.json()
    assert "symbol_concentration" in data
    assert "disclaimer" in data


def test_connect_endpoint_no_creds_returns_unconfigured():
    """Without real credentials, connect returns UNCONFIGURED provenance."""
    resp = client.post("/api/live/connect?provider=ZERODHA_KITE&is_mock=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["real_orders_disabled"] is True
    assert data["paper_trading_only"] is True
    # With no creds, provenance must be UNCONFIGURED or MOCK (not LIVE)
    assert data["data_provenance"] in ("UNCONFIGURED", "MOCK")


def test_disconnect_endpoint():
    resp = client.post("/api/live/disconnect?reason=Test+disconnect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is True


def test_tick_injection_rejects_zero_price():
    """Injecting a zero-price tick must return tick_rejected=True."""
    tick_data = {
        "symbol": "RELIANCE",
        "ltp": 0.0,  # Invalid!
        "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0,
        "volume": 0, "bid": 0.0, "ask": 0.0, "spread": 0.0,
        "timestamp": datetime.datetime.now().isoformat(),
        "is_live": False,
    }
    resp = client.post("/api/live/tick", json=tick_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("tick_rejected") is True
    assert data["gate"]["can_generate_signals"] is False


def test_tick_injection_valid_tick():
    """Valid tick should be accepted by the validator."""
    tick_data = {
        "symbol": "INFY",
        "ltp": 1700.0,
        "open": 1695.0, "high": 1710.0, "low": 1690.0, "close": 1700.0,
        "volume": 5000, "bid": 1699.0, "ask": 1701.0, "spread": 2.0,
        "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=1)).isoformat(),
        "is_live": False,
    }
    resp = client.post("/api/live/tick", json=tick_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("tick_rejected") is False


def test_validation_milestones_structure():
    resp = client.get("/api/live/validation-progress")
    data = resp.json()
    for m in data["milestones"]:
        assert "trades" in m
        assert "completed" in m
        assert "label" in m


def test_kill_switch_invalid_level():
    resp = client.post("/api/live/kill-switch/6?reason=test")
    assert resp.status_code == 400


def test_approve_nonexistent_signal_returns_400():
    resp = client.post("/api/live/signal/999999/approve")
    assert resp.status_code == 400


def test_reject_nonexistent_signal_returns_404():
    resp = client.post("/api/live/signal/999999/reject")
    assert resp.status_code == 404
