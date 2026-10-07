"""
Phase 8 — Zerodha Kite Connect v3 Adapter
Real-data market-data read-only adapter using httpx REST calls.
NO ORDER PLACEMENT. Market data only.

Credentials from environment:
  ZERODHA_API_KEY, ZERODHA_ACCESS_TOKEN

When credentials are not set: returns UNCONFIGURED (not MOCK).
When HTTP call fails: returns ERROR (never silently falls back to mock).
"""
import datetime
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings
from app.data.provider_response import ProviderResponse
from app.data.adapters.cache_manager import DataCacheManager

# Optional httpx import — gracefully handles missing package
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

KITE_BASE_URL = "https://api.kite.trade"
REQUEST_TIMEOUT_S = 5.0


class ZerodhaKiteAdapter:
    """
    Zerodha Kite Connect v3 Market Data Feed Adapter.
    Read-only. No order placement. No real-money execution.

    State transitions:
      UNCONFIGURED → no credentials in env
      LIVE          → successful authenticated HTTP response
      ERROR         → HTTP failure, timeout, malformed response
      MOCK is NEVER returned — this adapter fails closed.
    """

    def __init__(self):
        self.api_key = settings.ZERODHA_API_KEY
        self.access_token = settings.ZERODHA_ACCESS_TOKEN
        self.is_configured = bool(
            self.api_key and self.access_token
            and self.api_key not in ("your_zerodha_api_key_here", "")
            and self.access_token not in ("your_zerodha_access_token_here", "")
        )
        self._last_connection_test: Optional[Dict[str, Any]] = None

    def _auth_headers(self) -> Dict[str, str]:
        """Authorization header for Kite Connect v3."""
        return {
            "Authorization": f"token {self.api_key}:{self.access_token}",
            "X-Kite-Version": "3",
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Synchronous connection test.
        Returns UNCONFIGURED when credentials missing.
        Returns LIVE only after a verified HTTP round-trip.
        Returns ERROR on any failure.
        """
        ts = datetime.datetime.now().isoformat()
        if not self.is_configured:
            return {
                "provider": "ZERODHA_KITE",
                "connected": False,
                "status": "UNCONFIGURED",
                "error": "ZERODHA_API_KEY or ZERODHA_ACCESS_TOKEN not set in environment.",
                "timestamp": ts,
                "real_orders_disabled": True,
            }
        if not _HTTPX_AVAILABLE:
            return {
                "provider": "ZERODHA_KITE",
                "connected": False,
                "status": "ERROR",
                "error": "httpx package not available. Install httpx>=0.27.0.",
                "timestamp": ts,
                "real_orders_disabled": True,
            }
        try:
            start = datetime.datetime.now()
            with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
                resp = client.get(
                    f"{KITE_BASE_URL}/user/profile",
                    headers=self._auth_headers()
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000
            if resp.status_code == 200:
                return {
                    "provider": "ZERODHA_KITE",
                    "connected": True,
                    "status": "LIVE",
                    "latency_ms": round(latency_ms, 1),
                    "timestamp": ts,
                    "real_orders_disabled": True,
                }
            else:
                return {
                    "provider": "ZERODHA_KITE",
                    "connected": False,
                    "status": "ERROR",
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                    "timestamp": ts,
                    "real_orders_disabled": True,
                }
        except Exception as exc:
            return {
                "provider": "ZERODHA_KITE",
                "connected": False,
                "status": "ERROR",
                "error": f"Connection failed: {type(exc).__name__}: {str(exc)[:200]}",
                "timestamp": ts,
                "real_orders_disabled": True,
            }

    async def get_quote(self, symbol: str) -> ProviderResponse:
        """
        Fetch real-time quote for NSE symbol via Kite Connect REST.
        Returns UNCONFIGURED when no credentials.
        Returns ERROR (never MOCK) on any failure.
        """
        cache_key = f"ZERODHA_QUOTE_{symbol}"
        cached = DataCacheManager.get(cache_key)
        if cached:
            return cached

        if not self.is_configured:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ZERODHA_KITE_API",
                status="UNCONFIGURED",
                error="ZERODHA_API_KEY or ZERODHA_ACCESS_TOKEN not configured. Set in .env file."
            )

        if not _HTTPX_AVAILABLE:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ZERODHA_KITE_API",
                status="ERROR",
                error="httpx package not installed."
            )

        try:
            start = datetime.datetime.now()
            instrument = f"NSE:{symbol}"
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
                resp = await client.get(
                    f"{KITE_BASE_URL}/quote",
                    headers=self._auth_headers(),
                    params={"i": instrument}
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000

            if resp.status_code != 200:
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="ZERODHA_KITE_API",
                    status="ERROR",
                    error=f"Kite API HTTP {resp.status_code}: {resp.text[:200]}"
                )

            raw = resp.json()
            q = raw.get("data", {}).get(instrument, {})
            if not q:
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="ZERODHA_KITE_API",
                    status="ERROR",
                    error=f"No quote data returned for {instrument}"
                )

            ohlc = q.get("ohlc", {})
            depth = q.get("depth", {})
            best_bid = depth.get("buy", [{}])[0].get("price", 0.0) if depth else 0.0
            best_ask = depth.get("sell", [{}])[0].get("price", 0.0) if depth else 0.0

            quote_data = {
                "symbol": symbol,
                "instrument_token": str(q.get("instrument_token", "")),
                "exchange": "NSE",
                "current_price": float(q.get("last_price", 0.0)),
                "ltp": float(q.get("last_price", 0.0)),
                "open": float(ohlc.get("open", 0.0)),
                "high": float(ohlc.get("high", 0.0)),
                "low": float(ohlc.get("low", 0.0)),
                "close": float(ohlc.get("close", 0.0)),
                "volume": int(q.get("volume", 0)),
                "bid": float(best_bid),
                "ask": float(best_ask),
                "spread": round(float(best_ask) - float(best_bid), 2),
                "change_pct": float(q.get("change", 0.0)),
                "timestamp": q.get("timestamp", datetime.datetime.now().isoformat()),
                "latency_ms": round(latency_ms, 1),
                "data_provenance": "LIVE",
            }

            resp_obj = ProviderResponse.create(
                data=quote_data,
                source="ZERODHA_KITE_API",
                status="LIVE",
                latency_ms=round(latency_ms, 1)
            )
            DataCacheManager.set(cache_key, resp_obj, ttl_seconds=settings.CACHE_TTL_SECONDS)
            return resp_obj

        except httpx.TimeoutException:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ZERODHA_KITE_API",
                status="ERROR",
                error=f"Request timeout after {REQUEST_TIMEOUT_S}s"
            )
        except Exception as exc:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ZERODHA_KITE_API",
                status="ERROR",
                error=f"{type(exc).__name__}: {str(exc)[:200]}"
            )

    async def get_ltp(self, symbol: str) -> Optional[float]:
        """Convenience: get just the LTP. Returns None on any failure."""
        resp = await self.get_quote(symbol)
        if resp.status == "LIVE":
            return resp.data.get("ltp")
        return None
