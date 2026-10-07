"""
Phase 8 — Angel One SmartAPI Market Data Adapter
Read-only. No order placement. No real-money execution.

Credentials from environment:
  ANGELONE_API_KEY, ANGELONE_JWT_TOKEN (or ANGELONE_CLIENT_CODE + ANGELONE_PIN)

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

ANGELONE_BASE_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking"
REQUEST_TIMEOUT_S = 5.0

ANGEL_NSE_TOKENS: Dict[str, str] = {
    "RELIANCE": "2885",
    "TCS": "11536",
    "INFY": "1594",
    "HDFCBANK": "1333",
    "ICICIBANK": "4963",
    "SBIN": "3045",
    "TATAMOTORS": "3456",
    "ITC": "1660",
    "KOTAKBANK": "1922",
    "LT": "11483",
    "BHARTIARTL": "10604",
    "AXISBANK": "5900",
    "BAJFINANCE": "317",
    "MARUTI": "10999",
    "TATASTEEL": "3499",
    "WIPRO": "3787",
    "HINDUNILVR": "1394",
    "ASIANPAINT": "236",
    "TITAN": "3506",
    "SUNPHARMA": "3351",
}


class AngelOneSmartApiAdapter:
    """
    Angel One SmartAPI Market Data Adapter.
    Read-only. No order placement. PAPER TRADING ONLY.
    """

    def __init__(self):
        self.api_key = settings.ANGELONE_API_KEY
        self.client_code = settings.ANGELONE_CLIENT_CODE
        self.jwt_token = settings.ANGELONE_JWT_TOKEN
        self.is_configured = bool(
            self.api_key
            and self.jwt_token
            and self.api_key not in ("your_angelone_api_key_here", "")
            and self.jwt_token not in ("your_jwt_token_here", "")
        )

    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "apikey": self.api_key or "",
            "X-PrivateKey": self.api_key or "",
        }

    def test_connection(self) -> Dict[str, Any]:
        ts = datetime.datetime.now().isoformat()
        if not self.is_configured:
            return {
                "provider": "ANGEL_ONE", "connected": False, "status": "UNCONFIGURED",
                "error": "ANGELONE_API_KEY or ANGELONE_JWT_TOKEN not configured.",
                "timestamp": ts, "real_orders_disabled": True
            }
        if not _HTTPX_AVAILABLE:
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": "httpx not installed.", "timestamp": ts, "real_orders_disabled": True}
        try:
            start = datetime.datetime.now()
            with httpx.Client(timeout=REQUEST_TIMEOUT_S, verify=False) as client:
                resp = client.get(
                    f"{ANGELONE_BASE_URL}/user/v1/getProfile",
                    headers=self._auth_headers()
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000
            if resp.status_code == 200:
                return {"provider": "ANGEL_ONE", "connected": True, "status": "LIVE",
                        "latency_ms": round(latency_ms, 1), "timestamp": ts, "real_orders_disabled": True}
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": f"HTTP {resp.status_code}", "timestamp": ts, "real_orders_disabled": True}
        except Exception as exc:
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": str(exc)[:200], "timestamp": ts, "real_orders_disabled": True}

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> ProviderResponse:
        cache_key = f"ANGELONE_QUOTE_{symbol}"
        cached = DataCacheManager.get(cache_key)
        if cached:
            return cached

        if not self.is_configured:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ANGEL_ONE_SMARTAPI", status="UNCONFIGURED",
                error="ANGELONE_API_KEY or ANGELONE_JWT_TOKEN not set."
            )
        if not _HTTPX_AVAILABLE:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ANGEL_ONE_SMARTAPI", status="ERROR", error="httpx not installed."
            )

        token = ANGEL_NSE_TOKENS.get(symbol.upper(), symbol)
        try:
            payload = {"exchange": exchange, "tradingsymbol": symbol}
            start = datetime.datetime.now()
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, verify=False) as client:
                resp = await client.post(
                    f"{ANGELONE_BASE_URL}/market/v1/quote/",
                    headers=self._auth_headers(),
                    json={"mode": "LTP", "exchangeTokens": {exchange: [token]}}
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000

            if resp.status_code != 200:
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="ANGEL_ONE_SMARTAPI", status="ERROR",
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}"
                )

            raw = resp.json()
            if not raw.get("status", True) or not isinstance(raw.get("data"), dict):
                err_msg = raw.get("message") or "Token expired or invalid API response"
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="ANGEL_ONE_SMARTAPI", status="ERROR",
                    error=f"AngelOne: {err_msg}"
                )

            fetched = raw.get("data", {}).get("fetched", [])
            if not fetched:
                return ProviderResponse.create(
                    data={"symbol": symbol, "current_price": 0.0},
                    source="ANGEL_ONE_SMARTAPI", status="ERROR",
                    error="No quote data in response"
                )

            q = fetched[0]
            ltp = float(q.get("ltp", 0.0))

            quote_data = {
                "symbol": symbol, "exchange": exchange,
                "current_price": ltp, "ltp": ltp,
                "open": float(q.get("open", ltp)),
                "high": float(q.get("high", ltp)),
                "low": float(q.get("low", ltp)),
                "close": float(q.get("close", ltp)),
                "volume": int(q.get("tradeVolume", 0)),
                "bid": float(q.get("buyQty", 0.0)),
                "ask": float(q.get("sellQty", 0.0)),
                "spread": 0.0,
                "latency_ms": round(latency_ms, 1),
                "data_provenance": "LIVE",
            }

            resp_obj = ProviderResponse.create(
                data=quote_data, source="ANGEL_ONE_SMARTAPI", status="LIVE",
                latency_ms=int(round(latency_ms))
            )
            DataCacheManager.set(cache_key, resp_obj, ttl_seconds=settings.CACHE_TTL_SECONDS)
            return resp_obj

        except httpx.TimeoutException:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ANGEL_ONE_SMARTAPI", status="ERROR",
                error=f"Timeout after {REQUEST_TIMEOUT_S}s"
            )
        except Exception as exc:
            return ProviderResponse.create(
                data={"symbol": symbol, "current_price": 0.0},
                source="ANGEL_ONE_SMARTAPI", status="ERROR",
                error=f"{type(exc).__name__}: {str(exc)[:200]}"
            )
