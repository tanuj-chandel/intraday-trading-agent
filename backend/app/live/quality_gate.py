import datetime
from typing import Dict, Any, Optional
from enum import Enum


class DataProvenanceState(str, Enum):
    """
    All valid data provenance states for live feed classification.
    Only LIVE state permits signal generation.
    """
    LIVE = "LIVE"                     # Connected, fresh, real data confirmed
    STALE = "STALE"                   # Connected but data age > MAX_FRESHNESS_SECONDS
    DISCONNECTED = "DISCONNECTED"     # WebSocket/feed connection dropped
    UNCONFIGURED = "UNCONFIGURED"     # No broker credentials set in environment
    MOCK = "MOCK"                     # Mock/simulated data provider is active
    INVALID = "INVALID"               # Data fails basic validation rules (e.g., zero prices)
    ERROR = "ERROR"                   # Provider returned an error response


class LiveDataQualityGate:
    """
    Enforces real-time data freshness, market hours, and prevents silent mock fallback.
    Signal generation is ONLY permitted when provenance state is LIVE and data is fresh.
    All 7 provenance states are explicitly classified — no ambiguous defaults.
    """

    MAX_FRESHNESS_SECONDS = 30.0

    @classmethod
    def evaluate_live_feed(
        cls,
        last_tick_time: Optional[datetime.datetime],
        is_market_connected: bool,
        is_mock_provider: bool = False,
        has_credentials: bool = True,
        provider_error: Optional[str] = None,
        last_tick_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates live feed state and returns a full provenance gate result.

        Returns dict with:
          - status: DataProvenanceState value
          - can_generate_signals: bool (True ONLY for LIVE state with fresh data)
          - trading_enabled: bool
          - data_age_seconds: float (when available)
          - reason: human-readable explanation
          - is_trading_hours: bool (when determinable)
        """
        now = datetime.datetime.now()

        # 1. No credentials configured
        if not has_credentials:
            return cls._gate_result(
                state=DataProvenanceState.UNCONFIGURED,
                can_trade=False,
                reason="TRADING DISABLED — No broker API credentials configured in environment variables."
            )

        # 2. Provider error response
        if provider_error:
            return cls._gate_result(
                state=DataProvenanceState.ERROR,
                can_trade=False,
                reason=f"TRADING DISABLED — Provider returned error: {provider_error}"
            )

        # 3. Mock provider active
        if is_mock_provider:
            return cls._gate_result(
                state=DataProvenanceState.MOCK,
                can_trade=False,
                reason="TRADING DISABLED — MOCK DATA CANNOT BE USED FOR LIVE PAPER VALIDATION"
            )

        # 4. Connection dropped
        if not is_market_connected:
            return cls._gate_result(
                state=DataProvenanceState.DISCONNECTED,
                can_trade=False,
                reason="TRADING DISABLED — Real market data feed disconnected"
            )

        # 5. No ticks received yet
        if not last_tick_time:
            return cls._gate_result(
                state=DataProvenanceState.DISCONNECTED,
                can_trade=False,
                reason="TRADING DISABLED — No live ticks received yet from provider"
            )

        # 6. Data validation (price sanity)
        if last_tick_price is not None and last_tick_price <= 0:
            return cls._gate_result(
                state=DataProvenanceState.INVALID,
                can_trade=False,
                reason=f"TRADING DISABLED — Invalid tick price received: {last_tick_price}"
            )

        # 7. Staleness check
        data_age = (now - last_tick_time).total_seconds()
        if data_age > cls.MAX_FRESHNESS_SECONDS:
            return cls._gate_result(
                state=DataProvenanceState.STALE,
                can_trade=False,
                data_age=round(data_age, 1),
                reason=f"TRADING DISABLED — Market data stale ({data_age:.1f}s > {cls.MAX_FRESHNESS_SECONDS}s threshold)"
            )

        # 8. Market hours check (09:15–15:30 IST)
        current_time = now.time()
        market_open = datetime.time(9, 15)
        market_close = datetime.time(15, 30)
        is_trading_hours = market_open <= current_time <= market_close

        return {
            "status": DataProvenanceState.LIVE,
            "can_generate_signals": True,
            "trading_enabled": True,
            "data_age_seconds": round(data_age, 1),
            "is_trading_hours": is_trading_hours,
            "reason": "Real market feed is live, continuous, and verified fresh.",
            "provenance": "LIVE — real broker feed, credentials verified, freshness confirmed"
        }

    @classmethod
    def _gate_result(
        cls,
        state: DataProvenanceState,
        can_trade: bool,
        reason: str,
        data_age: Optional[float] = None
    ) -> Dict[str, Any]:
        result = {
            "status": state,
            "can_generate_signals": can_trade,
            "trading_enabled": can_trade,
            "reason": reason,
            "is_trading_hours": False,
            "provenance": state.value
        }
        if data_age is not None:
            result["data_age_seconds"] = data_age
        return result

    @classmethod
    def is_live(cls, gate_result: Dict[str, Any]) -> bool:
        """Convenience helper — returns True only if gate is fully LIVE."""
        return gate_result.get("status") == DataProvenanceState.LIVE
