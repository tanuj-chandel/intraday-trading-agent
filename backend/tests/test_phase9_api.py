"""
Phase 9 — API Endpoints Tests

Tests all 14 Phase 9 API endpoints: status, session lifecycle, trades,
statistics, comparison, regimes, time, concentration, data quality, verdict, and reports.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase9_status():
    resp = client.get("/api/phase9/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trading_mode"] == "PAPER_TRADING_ONLY"
    assert data["real_order_execution"] == "DISABLED"
    assert "data_mode" in data
    assert "badge" in data["data_mode"]


def test_phase9_session_current():
    resp = client.get("/api/phase9/session/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "session" in data
    assert data["session"]["status"] == "ACTIVE"


def test_phase9_sessions_list():
    resp = client.get("/api/phase9/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_phase9_trades_list():
    resp = client.get("/api/phase9/trades")
    assert resp.status_code == 200
    data = resp.json()
    assert "trades" in data
    assert "accounting_equation" in data


def test_phase9_statistics():
    resp = client.get("/api/phase9/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert "milestone" in data
    assert "bootstrap_95ci" in data
    assert "monte_carlo_forward" in data


def test_phase9_backtest_comparison():
    resp = client.get("/api/phase9/backtest-comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert "strategy_version" in data
    assert data["strategy_version"] == "VWAP_EMA_MOMENTUM_V1"


def test_phase9_regime_performance():
    resp = client.get("/api/phase9/regime-performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "regimes" in data


def test_phase9_time_performance():
    resp = client.get("/api/phase9/time-performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "time_slots" in data


def test_phase9_concentration():
    resp = client.get("/api/phase9/concentration")
    assert resp.status_code == 200
    data = resp.json()
    assert "concentration_risk" in data


def test_phase9_data_quality_impact():
    resp = client.get("/api/phase9/data-quality-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert "latency_breakdown" in data


def test_phase9_verdict():
    resp = client.get("/api/phase9/verdict")
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert data["verdict"] in [
        "INSUFFICIENT LIVE PAPER DATA",
        "EARLY PAPER EVIDENCE",
        "PRELIMINARY PAPER EVIDENCE",
        "EMPIRICAL PAPER EVIDENCE",
        "HIGH-CONFIDENCE PAPER CANDIDATE",
    ]


def test_phase9_session_lifecycle():
    # Start
    resp = client.post("/api/phase9/session/start?provider=ZERODHA_KITE")
    assert resp.status_code == 200
    start_data = resp.json()
    assert start_data["success"] is True

    # Close
    resp = client.post("/api/phase9/session/close?reason=TEST_COMPLETED")
    assert resp.status_code == 200
    close_data = resp.json()
    assert close_data["success"] is True
    assert "report_generated" in close_data


def test_phase9_reports_download():
    # Cumulative report endpoint
    resp = client.get("/api/phase9/report?report_type=cumulative")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
