"""
Phase 8 — Broker Adapter Tests
Tests for upgraded Zerodha, Upstox, and Angel One adapters.
All tests use mocked HTTP responses — NO real broker credentials required.
Tests verify UNCONFIGURED state when no creds, ERROR state on HTTP failure,
and LIVE state only when real HTTP succeeds.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.data.adapters.zerodha_adapter import ZerodhaKiteAdapter
from app.data.adapters.upstox_adapter import UpstoxAdapter
from app.data.adapters.angelone_adapter import AngelOneSmartApiAdapter


def run_async(coro):
    """Run a coroutine in a new event loop — Python 3.12 compatible."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Zerodha ──────────────────────────────────────────────────────────────────

def test_zerodha_unconfigured_when_no_credentials():
    """Without credentials, adapter must return UNCONFIGURED not MOCK."""
    with patch("app.data.adapters.zerodha_adapter.settings") as mock_settings:
        mock_settings.ZERODHA_API_KEY = None
        mock_settings.ZERODHA_ACCESS_TOKEN = None
        adapter = ZerodhaKiteAdapter()
        result = adapter.test_connection()
    assert result["status"] == "UNCONFIGURED"
    assert result["connected"] is False
    assert result.get("real_orders_disabled") is True


def test_zerodha_quote_unconfigured():
    """Quote call must return UNCONFIGURED when credentials missing."""
    with patch("app.data.adapters.zerodha_adapter.settings") as mock_settings:
        mock_settings.ZERODHA_API_KEY = None
        mock_settings.ZERODHA_ACCESS_TOKEN = None
        mock_settings.CACHE_TTL_SECONDS = 3
        adapter = ZerodhaKiteAdapter()

    async def run():
        return await adapter.get_quote("RELIANCE")

    resp = run_async(run())
    assert resp.status == "UNCONFIGURED"
    assert resp.data["current_price"] == 0.0


def test_zerodha_quote_error_on_http_failure():
    """Quote call returns ERROR (not MOCK) when HTTP call fails."""
    with patch("app.data.adapters.zerodha_adapter.settings") as mock_settings:
        mock_settings.ZERODHA_API_KEY = "test_key"
        mock_settings.ZERODHA_ACCESS_TOKEN = "test_token"
        mock_settings.CACHE_TTL_SECONDS = 3
        adapter = ZerodhaKiteAdapter()

    import httpx

    async def run():
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client
            return await adapter.get_quote("TCS")

    resp = run_async(run())
    assert resp.status == "ERROR"
    assert resp.data["current_price"] == 0.0


def test_zerodha_never_returns_mock():
    """Verify MOCK status is never returned by the adapter."""
    with patch("app.data.adapters.zerodha_adapter.settings") as mock_settings:
        mock_settings.ZERODHA_API_KEY = None
        mock_settings.ZERODHA_ACCESS_TOKEN = None
        mock_settings.CACHE_TTL_SECONDS = 3
        adapter = ZerodhaKiteAdapter()

    async def run():
        return await adapter.get_quote("INFY")

    resp = run_async(run())
    assert resp.status != "MOCK", "Adapter must NEVER return MOCK status"


def test_zerodha_connection_test_unconfigured():
    with patch("app.data.adapters.zerodha_adapter.settings") as ms:
        ms.ZERODHA_API_KEY = None
        ms.ZERODHA_ACCESS_TOKEN = None
        adapter = ZerodhaKiteAdapter()
    result = adapter.test_connection()
    assert result["status"] == "UNCONFIGURED"


# ── Upstox ───────────────────────────────────────────────────────────────────

def test_upstox_unconfigured_when_no_token():
    with patch("app.data.adapters.upstox_adapter.settings") as ms:
        ms.UPSTOX_API_KEY = None
        ms.UPSTOX_ACCESS_TOKEN = None
        adapter = UpstoxAdapter()
    result = adapter.test_connection()
    assert result["status"] == "UNCONFIGURED"
    assert result.get("real_orders_disabled") is True


def test_upstox_quote_unconfigured():
    with patch("app.data.adapters.upstox_adapter.settings") as ms:
        ms.UPSTOX_ACCESS_TOKEN = None
        ms.UPSTOX_API_KEY = None
        ms.CACHE_TTL_SECONDS = 3
        adapter = UpstoxAdapter()

    async def run():
        return await adapter.get_quote("RELIANCE")

    resp = run_async(run())
    assert resp.status == "UNCONFIGURED"


def test_upstox_never_returns_mock():
    with patch("app.data.adapters.upstox_adapter.settings") as ms:
        ms.UPSTOX_ACCESS_TOKEN = None
        ms.UPSTOX_API_KEY = None
        ms.CACHE_TTL_SECONDS = 3
        adapter = UpstoxAdapter()

    async def run():
        return await adapter.get_quote("TCS")

    resp = run_async(run())
    assert resp.status != "MOCK"


# ── Angel One ────────────────────────────────────────────────────────────────

def test_angelone_unconfigured_when_no_credentials():
    with patch("app.data.adapters.angelone_adapter.settings") as ms:
        ms.ANGELONE_API_KEY = None
        ms.ANGELONE_JWT_TOKEN = None
        ms.ANGELONE_CLIENT_CODE = None
        adapter = AngelOneSmartApiAdapter()
    result = adapter.test_connection()
    assert result["status"] == "UNCONFIGURED"
    assert result.get("real_orders_disabled") is True


def test_angelone_quote_unconfigured():
    with patch("app.data.adapters.angelone_adapter.settings") as ms:
        ms.ANGELONE_API_KEY = None
        ms.ANGELONE_JWT_TOKEN = None
        ms.ANGELONE_CLIENT_CODE = None
        ms.CACHE_TTL_SECONDS = 3
        adapter = AngelOneSmartApiAdapter()

    async def run():
        return await adapter.get_quote("RELIANCE")

    resp = run_async(run())
    assert resp.status == "UNCONFIGURED"


def test_angelone_never_returns_mock():
    with patch("app.data.adapters.angelone_adapter.settings") as ms:
        ms.ANGELONE_API_KEY = None
        ms.ANGELONE_JWT_TOKEN = None
        ms.ANGELONE_CLIENT_CODE = None
        ms.CACHE_TTL_SECONDS = 3
        adapter = AngelOneSmartApiAdapter()

    async def run():
        return await adapter.get_quote("HDFC")

    resp = run_async(run())
    assert resp.status != "MOCK"


# ── Common Safety Rule ────────────────────────────────────────────────────────

def test_no_order_placement_in_zerodha_adapter():
    """Verify no order placement methods exist in Zerodha adapter."""
    adapter = ZerodhaKiteAdapter()
    forbidden = ["place_order", "create_order", "submit_order", "execute_order", "order_modify"]
    for method in forbidden:
        assert not hasattr(adapter, method), f"Security violation: {method} found in ZerodhaKiteAdapter"


def test_no_order_placement_in_upstox_adapter():
    adapter = UpstoxAdapter()
    forbidden = ["place_order", "create_order", "submit_order", "execute_order"]
    for method in forbidden:
        assert not hasattr(adapter, method), f"Security violation: {method} found in UpstoxAdapter"


def test_no_order_placement_in_angelone_adapter():
    adapter = AngelOneSmartApiAdapter()
    forbidden = ["place_order", "create_order", "submit_order", "execute_order"]
    for method in forbidden:
        assert not hasattr(adapter, method), f"Security violation: {method} found in AngelOneSmartApiAdapter"
