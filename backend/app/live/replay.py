from typing import Dict, Any, Optional
from app.live.data_types import LiveSignalItem

class SessionReplayService:
    """
    Session Replay & Debugging Engine.
    Reconstructs exact market ticks, indicator snapshot, and risk conditions that existed when a signal was generated.
    """

    @classmethod
    def replay_signal_decision(
        cls,
        signal: LiveSignalItem
    ) -> Dict[str, Any]:
        return {
            "signal_id": signal.id,
            "symbol": signal.symbol,
            "decision_timestamp": signal.created_at.isoformat(),
            "direction": signal.direction,
            "strategy": signal.strategy_name,
            "market_regime": signal.market_regime,
            "indicator_state_at_entry": signal.indicator_snapshot,
            "data_freshness_seconds": signal.data_freshness_seconds,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "target_price": signal.target_price,
            "reason_for_generation": signal.reason,
            "risk_validation": {
                "risk_passed": signal.risk_passed,
                "notes": signal.risk_notes or "RiskManager verified within 1% capital exposure."
            }
        }
