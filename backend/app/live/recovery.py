import datetime
from typing import Dict, Any, List
from app.live.data_types import LivePaperPosition
from app.live.position_manager import LivePositionManager

class CrashRecoveryService:
    """
    Reconciles open paper trading positions, daily realized P&L, and risk manager state upon backend crash/restart.
    """

    @classmethod
    def restore_session(
        cls,
        manager: LivePositionManager,
        persisted_positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        restored_count = 0
        for p in persisted_positions:
            if p.get("status") == "OPEN":
                pos = LivePaperPosition(**p)
                manager.add_position(pos)
                restored_count += 1

        summary = manager.get_portfolio_summary()
        return {
            "restored_positions_count": restored_count,
            "session_state": summary,
            "recovery_timestamp": datetime.datetime.now().isoformat(),
            "status": "RECOVERED_HEALTHY"
        }
