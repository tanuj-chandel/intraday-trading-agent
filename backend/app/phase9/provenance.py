"""
Phase 9 — Enhanced Real Market Data Provenance & Mode Indicator

Enforces strict separation between genuine LIVE data and MOCK/SAMPLE/SIMULATED data.
Every observation retains complete provenance metadata.
Signals are ONLY allowed when provenance is strictly LIVE.
"""
import datetime
from enum import Enum
from typing import Dict, Any, Optional
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Phase9ProvenanceState(str, Enum):
    """
    7 explicit data provenance classifications.
    Only LIVE state permits paper trade signal generation.
    """
    LIVE = "LIVE"                     # Genuine authenticated real-time market data
    STALE = "STALE"                   # Real connection active, but tick age > 30s
    MOCK = "MOCK"                     # Synthetic/mock provider active
    SAMPLE = "SAMPLE"                 # Demo/sample historical slice
    MANUAL = "MANUAL"                 # Operator injected/manual tick
    ERROR = "ERROR"                   # Feed returned error or malformed payload
    UNCONFIGURED = "UNCONFIGURED"     # No broker API credentials set


class Phase9UIMode(str, Enum):
    """
    4-tier prominent UI mode indicator.
    Makes it impossible to confuse real data with simulated data.
    """
    LIVE_MARKET_DATA = "LIVE MARKET DATA"         # 🟢 LIVE
    STALE_DATA = "STALE DATA"                     # 🟡 STALE
    NO_LIVE_DATA = "NO LIVE DATA"                 # 🔴 ERROR / DISCONNECTED / UNCONFIGURED
    MOCK_SIMULATION = "MOCK / SIMULATION"         # ⚪ MOCK / SAMPLE / MANUAL


class Phase9ProvenanceEngine:
    """
    Evaluates feed state, decorates ticks with full audit metadata,
    and determines UI indicators and signal generation safety gates.
    """

    MAX_FRESHNESS_SECONDS = 30.0

    @classmethod
    def get_ui_indicator(cls, state: Phase9ProvenanceState) -> Dict[str, str]:
        """Map provenance state to prominent UI status indicator."""
        if state == Phase9ProvenanceState.LIVE:
            return {
                "mode": Phase9UIMode.LIVE_MARKET_DATA.value,
                "badge": "🟢 LIVE MARKET DATA",
                "color": "emerald",
                "description": "Authenticated genuine live NSE/BSE market feed."
            }
        elif state == Phase9ProvenanceState.STALE:
            return {
                "mode": Phase9UIMode.STALE_DATA.value,
                "badge": "🟡 STALE DATA",
                "color": "amber",
                "description": "Market connection active, but tick freshness exceeded threshold (>30s)."
            }
        elif state in (Phase9ProvenanceState.MOCK, Phase9ProvenanceState.SAMPLE, Phase9ProvenanceState.MANUAL):
            return {
                "mode": Phase9UIMode.MOCK_SIMULATION.value,
                "badge": "⚪ MOCK / SIMULATION",
                "color": "slate",
                "description": "Simulation or testing data feed. Real signals strictly blocked."
            }
        else:
            return {
                "mode": Phase9UIMode.NO_LIVE_DATA.value,
                "badge": "🔴 NO LIVE DATA",
                "color": "rose",
                "description": "No live broker data feed active. Signals strictly blocked."
            }

    @classmethod
    def classify_feed(
        cls,
        is_connected: bool,
        is_mock: bool,
        has_credentials: bool,
        last_tick_time: Optional[datetime.datetime],
        last_tick_price: Optional[float] = None,
        provider_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate provenance state. Returns classification dict with can_generate_signals gate.
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        # 1. No credentials configured
        if not has_credentials:
            state = Phase9ProvenanceState.UNCONFIGURED
            reason = "No broker API credentials configured in environment."
        # 2. Provider error
        elif provider_error:
            state = Phase9ProvenanceState.ERROR
            reason = f"Provider error: {provider_error}"
        # 3. Mock provider
        elif is_mock:
            state = Phase9ProvenanceState.MOCK
            reason = "Mock provider active. Real market data is not connected."
        # 4. Disconnected
        elif not is_connected:
            state = Phase9ProvenanceState.ERROR
            reason = "Market data feed disconnected."
        # 5. Invalid price
        elif last_tick_price is not None and last_tick_price <= 0:
            state = Phase9ProvenanceState.ERROR
            reason = f"Invalid tick price: {last_tick_price}"
        # 6. Check freshness
        elif last_tick_time is not None:
            if last_tick_time.tzinfo:
                now_cmp = datetime.datetime.now(tz=datetime.timezone.utc)
                age = max(0.0, (now_cmp - last_tick_time).total_seconds())
            else:
                now_cmp = datetime.datetime.now()
                age = max(0.0, (now_cmp - last_tick_time).total_seconds())

            if age > cls.MAX_FRESHNESS_SECONDS:
                state = Phase9ProvenanceState.STALE
                reason = f"Data stale: last tick age {age:.1f}s exceeds threshold ({cls.MAX_FRESHNESS_SECONDS}s)."
            else:
                state = Phase9ProvenanceState.LIVE
                reason = f"Genuine live market data confirmed (freshness: {age:.1f}s)."
        else:
            state = Phase9ProvenanceState.ERROR
            reason = "No tick received yet from connected provider."

        can_generate_signals = (state == Phase9ProvenanceState.LIVE)
        ui = cls.get_ui_indicator(state)

        return {
            "state": state.value,
            "can_generate_signals": can_generate_signals,
            "reason": reason,
            "ui_indicator": ui,
            "timestamp": now.isoformat(),
        }

    @classmethod
    def decorate_observation(
        cls,
        symbol: str,
        price: float,
        provider: str,
        exchange: str = "NSE",
        source: str = "REST_API",
        state: Phase9ProvenanceState = Phase9ProvenanceState.LIVE,
        latency_ms: float = 0.0,
        tick_timestamp: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Attach full provenance metadata to every observation record.
        """
        now = datetime.datetime.now(tz=IST)
        ts = tick_timestamp or now
        ts_utc = ts.astimezone(pytz.utc) if ts.tzinfo else pytz.utc.localize(ts)
        now_utc = datetime.datetime.now(tz=pytz.utc)
        freshness_s = max(0.0, (now_utc - ts_utc).total_seconds())

        return {
            "provider": provider,
            "symbol": symbol,
            "exchange": exchange,
            "price": price,
            "timestamp": ts.isoformat(),
            "timezone": "Asia/Kolkata",
            "source": source,
            "provenance_state": state.value,
            "latency_ms": round(latency_ms, 1),
            "freshness_seconds": round(freshness_s, 2),
            "validation_status": "VALID" if price > 0 and state == Phase9ProvenanceState.LIVE else "UNVERIFIED",
            "is_genuine_live": (state == Phase9ProvenanceState.LIVE)
        }
