"""
Phase 8 — Upstox v2 REST Market Data Adapter
Read-only. No order placement. No real-money execution.

Credentials from environment:
  UPSTOX_API_KEY, UPSTOX_ACCESS_TOKEN

When credentials missing: UNCONFIGURED (not MOCK).
When HTTP fails: ERROR (never silent mock fallback).
"""
import datetime
from typing import Dict, Any, Optional
from app.core.config import settings
from app.data.provider_response import ProviderResponse
from app.data.adapters.cache_manager import DataCacheManager

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

UPSTOX_BASE_URL = "https://api.upstox.com/v2"
REQUEST_TIMEOUT_S = 5.0


class UpstoxAdapter:
    """
    Upstox API v2 Market Data Adapter.
    Read-only. No order placement. PAPER TRADING ONLY.
    """

    def __init__(self):
        self.api_key = settings.UPSTOX_API_KEY
        self.access_token = settings.UPSTOX_ACCESS_TOKEN
        self.is_configured = bool(
            self.access_token
            and self.access_token not in ("your_upstox_access_token_here", "")
        )

    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def _instrument_key(self, symbol: str) -> str:
        """Convert symbol to Upstox NSE instrument key."""
        return f"NSE_EQ|{symbol}"

    def test_connection(self) -> Dict[str, Any]:
        ts = datetime.datetime.now().isoformat()
        if not self.is_configured:
            return {
                "provider": "UPSTOX", "connected": False, "status": "UNCONFIGURED",
                "error": "UPSTOX_ACCESS_TOKEN not configured in environment.",
                "timestamp": ts, "real_orders_disabled": True
            }
        if not _HTTPX_AVAILABLE:
            return {"provider": "UPSTOX", "connected": False, "status": "ERROR",
                    "error": "httpx not installed.", "timestamp": ts, "real_orders_disabled": True}
        try:
            start = datetime.datetime.now()
            with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
                resp = client.get(f"{UPSTOX_BASE_URL}/user/profile", headers=self._auth_headers())
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000
            if resp.status_code == 200:
                return {"provider": "UPSTOX", "connected": True, "status": "LIVE",
                        "latency_ms": round(latency_ms, 1), "timestamp": ts, "real_orders_disabled": True}
            return {"provider": "UPSTOX", "connected": False, "status": "ERROR",
                    "error": f"HTTP {resp.status_code}", "timestamp": ts, "real_orders_disabled": True}
        except Exception as exc:
            return {"provider": "UPSTOX", "connected": False, "status": "ERROR",
                    "error": str(exc)[:200], "timestamp": ts, "real_orders_disabled": True}

    async def get_quote(self, symbol: str) -> ProviderResponse:
        cache_key = f"UPSTOX_QUOTE_{symbol}"
        cached = DataCacheManager.get(cache_key)
        if cached:
            return cached

        if not self.is_configured:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="UPSTOX_API_V2", status="UNCONFIGURED",
                error="UPSTOX_ACCESS_TOKEN not set."
            )
        if not _HTTPX_AVAILABLE:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="UPSTOX_API_V2", status="ERROR", error="httpx not installed."
            )

        try:
            instrument_key = self._instrument_key(symbol)
            start = datetime.datetime.now()
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
                resp = await client.get(
                    f"{UPSTOX_BASE_URL}/market-quote/ltp",
                    headers=self._auth_headers(),
                    params={"instrument_key": instrument_key}
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000

            if resp.status_code != 200:
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="UPSTOX_API_V2", status="ERROR",
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}"
                )

            raw = resp.json()
            data_section = raw.get("data", {}).get(instrument_key, {})
            ltp = float(data_section.get("last_price", 0.0))

            # Also fetch OHLC from full quote endpoint
            ohlc_resp = await client.get(
                f"{UPSTOX_BASE_URL}/market-quote/quotes",
                headers=self._auth_headers(),
                params={"instrument_key": instrument_key}
            ) if _HTTPX_AVAILABLE else None

            ohlc_data = {}
            if ohlc_resp and ohlc_resp.status_code == 200:
                ohlc_raw = ohlc_resp.json().get("data", {}).get(instrument_key, {})
                ohlc_data = ohlc_raw.get("ohlc", {})

            quote_data = {
                "symbol": symbol, "exchange": "NSE",
                "current_price": ltp, "ltp": ltp,
                "open": float(ohlc_data.get("open", ltp)),
                "high": float(ohlc_data.get("high", ltp)),
                "low": float(ohlc_data.get("low", ltp)),
                "close": float(ohlc_data.get("close", ltp)),
                "volume": int(data_section.get("volume", 0)),
                "bid": float(data_section.get("bid_price", 0.0)),
                "ask": float(data_section.get("ask_price", 0.0)),
                "spread": round(float(data_section.get("ask_price", 0.0)) - float(data_section.get("bid_price", 0.0)), 2),
                "latency_ms": round(latency_ms, 1),
                "data_provenance": "LIVE",
            }

            resp_obj = ProviderResponse.create(
                data=quote_data, source="UPSTOX_API_V2", status="LIVE",
                latency_ms=round(latency_ms, 1)
            )
            DataCacheManager.set(cache_key, resp_obj, ttl_seconds=settings.CACHE_TTL_SECONDS)
            return resp_obj

        except httpx.TimeoutException:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="UPSTOX_API_V2", status="ERROR",
                error=f"Request timeout after {REQUEST_TIMEOUT_S}s"
            )
        except Exception as exc:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="UPSTOX_API_V2", status="ERROR",
                error=f"{type(exc).__name__}: {str(exc)[:200]}"
            )
