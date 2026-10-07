import pytest
from app.data.health_checker import DataProviderHealthChecker

def test_data_provider_health_check_structure():
    health = DataProviderHealthChecker.check_all_providers()
    assert "checked_at" in health
    assert "market_data" in health
    assert "news" in health
    assert "global_markets" in health
    assert "gift_nifty" in health
    assert "corporate_announcements" in health
    assert "market_calendar" in health
    assert health["overall_health"] in ["HEALTHY", "DEGRADED"]

def test_market_data_unconfigured_status():
    # Without real broker credentials, status must be MOCK or UNAVAILABLE (never falsely LIVE)
    health = DataProviderHealthChecker.check_all_providers()
    mkt = health["market_data"]
    assert mkt["status"] in ["MOCK", "HISTORICAL", "UNAVAILABLE"]
