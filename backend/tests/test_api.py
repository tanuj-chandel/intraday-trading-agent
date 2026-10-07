import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_api(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mode"] == "PAPER_TRADING_ONLY"

def test_market_overview_api(client):
    response = client.get("/api/market/overview")
    assert response.status_code == 200
    data = response.json()
    assert len(data["indices"]) >= 2
    assert "market_regime" in data

def test_top_stocks_api(client):
    response = client.get("/api/stocks/top?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10
    assert len(data) > 0
    assert "total_score" in data[0]

def test_premarket_analyze_api(client):
    response = client.post("/api/premarket/analyze")
    assert response.status_code == 200
    data = response.json()
    assert "top_ranked_stocks" in data
    assert len(data["top_ranked_stocks"]) == 10

def test_generate_and_approve_signal_api(client):
    # 1. Generate signals
    gen_res = client.post("/api/signals/generate")
    assert gen_res.status_code == 200
    signals = gen_res.json()
    
    if len(signals) > 0:
        sig_id = signals[0]["id"]
        # 2. Approve signal
        app_res = client.post(f"/api/signals/{sig_id}/approve")
        assert app_res.status_code == 200
        assert "success" in app_res.json()

def test_performance_api(client):
    response = client.get("/api/performance")
    assert response.status_code == 200
    data = response.json()
    assert "win_rate_pct" in data
    assert "current_equity" in data
