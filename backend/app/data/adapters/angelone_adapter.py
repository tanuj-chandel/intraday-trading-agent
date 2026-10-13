"""
Phase 8 — Angel One SmartAPI Market Data Adapter (patched)
Read-only. No order placement. No real-money execution.

Changes vs. previous version:
  * Tokens can be injected at runtime (from AngelOneAuth) instead of a stale .env JWT.
  * Quote mode is FULL (LTP mode returns no OHLC/volume, which made RVOL permanently 1.0).
  * get_quotes() fetches all symbols in ONE request (Angel allows up to 50 tokens).
  * Volume is converted from cumulative day volume to per-tick delta.
  * bid/ask come from the order-book depth prices, not buyQty/sellQty.
  * get_historical_candles() added for indicator warm-up.

When credentials missing: UNCONFIGURED (not MOCK).
When HTTP fails: ERROR (never silent mock fallback).
"""
import datetime
from typing import Dict, Any, Optional, List

import pytz

from app.core.config import settings
from app.core.logging import logger
from app.data.provider_response import ProviderResponse

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

IST = pytz.timezone("Asia/Kolkata")
ANGELONE_BASE_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking"
REQUEST_TIMEOUT_S = 5.0

# NSE equity symbol tokens. Add any symbol you trade here; unknown symbols are skipped
# with a loud warning instead of being sent to the API as a bogus token.
ANGEL_NSE_TOKENS: Dict[str, str] = {
    "RELIANCE": "2885", "TCS": "11536", "INFY": "1594", "HDFCBANK": "1333",
    "ICICIBANK": "4963", "SBIN": "3045", "TATAMOTORS": "3456", "ITC": "1660",
    "KOTAKBANK": "1922", "LT": "11483", "BHARTIARTL": "10604", "AXISBANK": "5900",
    "BAJFINANCE": "317", "MARUTI": "10999", "TATASTEEL": "3499", "WIPRO": "3787",
    "HINDUNILVR": "1394", "ASIANPAINT": "236", "TITAN": "3506", "SUNPHARMA": "3351",
}
TOKEN_TO_SYMBOL: Dict[str, str] = {v: k for k, v in ANGEL_NSE_TOKENS.items()}

INTERVAL_MAP = {"1m": "ONE_MINUTE", "5m": "FIVE_MINUTE", "15m": "FIFTEEN_MINUTE"}


class AngelOneSmartApiAdapter:
    """
    Angel One SmartAPI Market Data Adapter.
    Read-only. No order placement. PAPER TRADING ONLY.
    """

    def __init__(self, jwt_token: Optional[str] = None, feed_token: Optional[str] = None):
        self.api_key = settings.ANGELONE_API_KEY
        self.client_code = settings.ANGELONE_CLIENT_CODE
        # Runtime-injected token wins over the static .env token.
        self.jwt_token = jwt_token or settings.ANGELONE_JWT_TOKEN
        self.feed_token = feed_token
        # Per-symbol cumulative volume from the last quote, used to compute tick deltas.
        self._last_cum_volume: Dict[str, int] = {}
        self._last_feed_time: Dict[str, str] = {}

    @property
    def is_configured(self) -> bool:
        return bool(
            self.api_key and self.jwt_token
            and self.api_key not in ("your_angelone_api_key_here", "")
            and self.jwt_token not in ("your_jwt_token_here", "")
        )

    def set_tokens(self, jwt_token: str, feed_token: Optional[str] = None) -> None:
        self.jwt_token = jwt_token
        if feed_token:
            self.feed_token = feed_token

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
            "X-PrivateKey": self.api_key or "",
        }

    def _error(self, symbol: str, msg: str) -> ProviderResponse:
        return ProviderResponse.create(
            data={"symbol": symbol, "current_price": 0.0},
            source="ANGEL_ONE_SMARTAPI", status="ERROR", error=msg,
        )

    # ------------------------------------------------------------------ health

    def test_connection(self) -> Dict[str, Any]:
        ts = datetime.datetime.now().isoformat()
        if not self.is_configured:
            return {"provider": "ANGEL_ONE", "connected": False, "status": "UNCONFIGURED",
                    "error": "ANGELONE_API_KEY or JWT token not configured.",
                    "timestamp": ts, "real_orders_disabled": True}
        if not _HTTPX_AVAILABLE:
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": "httpx not installed.", "timestamp": ts, "real_orders_disabled": True}
        try:
            start = datetime.datetime.now()
            with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
                resp = client.get(f"{ANGELONE_BASE_URL}/user/v1/getProfile", headers=self._auth_headers())
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000
            if resp.status_code == 200 and resp.json().get("status"):
                return {"provider": "ANGEL_ONE", "connected": True, "status": "LIVE",
                        "latency_ms": round(latency_ms, 1), "timestamp": ts, "real_orders_disabled": True}
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": f"HTTP {resp.status_code}: {resp.text[:120]}", "timestamp": ts,
                    "real_orders_disabled": True}
        except Exception as exc:
            return {"provider": "ANGEL_ONE", "connected": False, "status": "ERROR",
                    "error": str(exc)[:200], "timestamp": ts, "real_orders_disabled": True}

    # ------------------------------------------------------------------ quotes

    def _parse_full_quote(self, q: Dict[str, Any], symbol: str, latency_ms: float) -> Dict[str, Any]:
        ltp = float(q.get("ltp", 0.0))
        cum_vol = int(q.get("tradeVolume", 0) or 0)

        # Cumulative day volume -> per-tick delta. First observation contributes 0
        # so that the whole morning's volume isn't dumped into one candle.
        prev = self._last_cum_volume.get(symbol)
        if prev is None or cum_vol < prev:
            delta_vol = 0
        else:
            delta_vol = cum_vol - prev
        self._last_cum_volume[symbol] = cum_vol

        depth = q.get("depth") or {}
        buy_lvls = depth.get("buy") or []
        sell_lvls = depth.get("sell") or []
        bid = float(buy_lvls[0].get("price", 0.0)) if buy_lvls else 0.0
        ask = float(sell_lvls[0].get("price", 0.0)) if sell_lvls else 0.0
        if bid <= 0:
            bid = round(ltp * 0.9998, 2)
        if ask <= 0:
            ask = round(ltp * 1.0002, 2)

        feed_time = str(q.get("exchFeedTime", ""))
        self._last_feed_time[symbol] = feed_time

        return {
            "symbol": symbol, "exchange": "NSE",
            "current_price": ltp, "ltp": ltp,
            "open": float(q.get("open", ltp) or ltp),
            "high": float(q.get("high", ltp) or ltp),
            "low": float(q.get("low", ltp) or ltp),
            # NOTE: Angel's "close" is the PREVIOUS day's close. Exposed as prev_close;
            # callers must use ltp for the candle "close" or the tick validator rejects it.
            "prev_close": float(q.get("close", ltp) or ltp),
            "close": ltp,
            "volume": delta_vol,
            "cumulative_volume": cum_vol,
            "bid": bid, "ask": ask,
            "spread": round(max(0.0, ask - bid), 2),
            "exch_feed_time": feed_time,
            "latency_ms": round(latency_ms, 1),
            "data_provenance": "LIVE",
        }

    async def get_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, ProviderResponse]:
        """
        Fetch FULL quotes for many symbols in a single request.
        Returns {symbol: ProviderResponse}. Every requested symbol gets an entry.
        """
        result: Dict[str, ProviderResponse] = {}
        if not self.is_configured:
            for s in symbols:
                result[s] = ProviderResponse.create(
                    data={"symbol": s, "current_price": 0.0}, source="ANGEL_ONE_SMARTAPI",
                    status="UNCONFIGURED", error="Angel One token not set.")
            return result
        if not _HTTPX_AVAILABLE:
            for s in symbols:
                result[s] = self._error(s, "httpx not installed.")
            return result

        tokens: List[str] = []
        for s in symbols:
            tok = ANGEL_NSE_TOKENS.get(s.upper())
            if tok:
                tokens.append(tok)
            else:
                logger.error(f"Angel One: no NSE token mapped for {s}; add it to ANGEL_NSE_TOKENS.")
                result[s] = self._error(s, "No symbol token mapped.")
        if not tokens:
            return result

        try:
            start = datetime.datetime.now()
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
                resp = await client.post(
                    f"{ANGELONE_BASE_URL}/market/v1/quote/",
                    headers=self._auth_headers(),
                    json={"mode": "FULL", "exchangeTokens": {exchange: tokens}},
                )
            latency_ms = (datetime.datetime.now() - start).total_seconds() * 1000
        except httpx.TimeoutException:
            for s in symbols:
                result.setdefault(s, self._error(s, f"Timeout after {REQUEST_TIMEOUT_S}s"))
            return result
        except Exception as exc:
            for s in symbols:
                result.setdefault(s, self._error(s, f"{type(exc).__name__}: {str(exc)[:160]}"))
            return result

        if resp.status_code != 200:
            msg = f"HTTP {resp.status_code}: {resp.text[:160]}"
            for s in symbols:
                result.setdefault(s, self._error(s, msg))
            return result

        raw = resp.json()
        if not raw.get("status", False) or not isinstance(raw.get("data"), dict):
            msg = f"AngelOne: {raw.get('message') or 'token expired or bad response'}"
            for s in symbols:
                result.setdefault(s, self._error(s, msg))
            return result

        fetched = raw["data"].get("fetched", []) or []
        unfetched = raw["data"].get("unfetched", []) or []

        for q in fetched:
            sym = TOKEN_TO_SYMBOL.get(str(q.get("symbolToken", "")), "")
            if not sym:
                ts = str(q.get("tradingSymbol", "")).replace("-EQ", "")
                sym = ts if ts in ANGEL_NSE_TOKENS else ""
            if not sym:
                continue
            data = self._parse_full_quote(q, sym, latency_ms)
            if data["ltp"] <= 0:
                result[sym] = self._error(sym, "LTP is zero.")
                continue
            result[sym] = ProviderResponse.create(
                data=data, source="ANGEL_ONE_SMARTAPI", status="LIVE", latency_ms=int(round(latency_ms)))

        for u in unfetched:
            sym = TOKEN_TO_SYMBOL.get(str(u.get("symbolToken", "")), "")
            if sym:
                result[sym] = self._error(sym, f"Unfetched: {u.get('message', 'unknown')}")

        for s in symbols:
            result.setdefault(s, self._error(s, "Symbol missing from quote response."))
        return result

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> ProviderResponse:
        """Single-symbol convenience wrapper (kept for backward compatibility)."""
        res = await self.get_quotes([symbol], exchange=exchange)
        return res.get(symbol, self._error(symbol, "No response."))

    # -------------------------------------------------------------- historical

    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: str = "5m",
        from_dt: Optional[datetime.datetime] = None,
        to_dt: Optional[datetime.datetime] = None,
        exchange: str = "NSE",
    ) -> List[Dict[str, Any]]:
        """
        Returns completed candles as dicts: {timestamp(datetime IST, naive), open, high, low, close, volume}.
        Used to warm up EMA/MACD/RVOL before the first live 5m bar closes.
        Angel rate limit for this endpoint is ~3 req/s; call sequentially.
        """
        if not self.is_configured or not _HTTPX_AVAILABLE:
            return []
        tok = ANGEL_NSE_TOKENS.get(symbol.upper())
        if not tok:
            logger.error(f"Angel One history: no token for {symbol}")
            return []
        interval = INTERVAL_MAP.get(timeframe)
        if not interval:
            return []

        now_ist = datetime.datetime.now(tz=IST)
        to_dt = to_dt or now_ist
        from_dt = from_dt or (to_dt - datetime.timedelta(days=4))
        payload = {
            "exchange": exchange,
            "symboltoken": tok,
            "interval": interval,
            "fromdate": from_dt.strftime("%Y-%m-%d %H:%M"),
            "todate": to_dt.strftime("%Y-%m-%d %H:%M"),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{ANGELONE_BASE_URL}/historical/v1/getCandleData",
                    headers=self._auth_headers(), json=payload)
            if resp.status_code != 200:
                logger.error(f"Angel One history {symbol}: HTTP {resp.status_code} {resp.text[:120]}")
                return []
            raw = resp.json()
            if not raw.get("status") or not isinstance(raw.get("data"), list):
                logger.error(f"Angel One history {symbol}: {raw.get('message', 'bad response')}")
                return []
            out = []
            for row in raw["data"]:
                # ["2024-01-01T09:15:00+05:30", o, h, l, c, v]
                ts = datetime.datetime.fromisoformat(row[0]).astimezone(IST).replace(tzinfo=None)
                out.append({"timestamp": ts, "open": float(row[1]), "high": float(row[2]),
                            "low": float(row[3]), "close": float(row[4]), "volume": int(row[5])})
            return out
        except Exception as exc:
            logger.error(f"Angel One history {symbol}: {type(exc).__name__}: {exc}")
            return []
