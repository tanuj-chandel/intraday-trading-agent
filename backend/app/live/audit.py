import datetime
from typing import List, Dict, Any, Optional
from app.live.data_types import LiveAuditEvent


class LiveAuditLogger:
    """
    Dual-write audit logger for live paper trading:
    - In-memory ring buffer for fast real-time reads (API/SSE)
    - DB write to system_logs table for crash recovery and permanent audit trail

    DB writes are best-effort; failures do not block trading operations.
    """

    _events: List[LiveAuditEvent] = []
    _event_counter = 0

    @classmethod
    def log(
        cls,
        event_type: str,
        details: str,
        symbol: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LiveAuditEvent:
        cls._event_counter += 1
        event = LiveAuditEvent(
            id=cls._event_counter,
            event_type=event_type,
            symbol=symbol,
            details=details,
            timestamp=datetime.datetime.now(),
            metadata=metadata or {}
        )
        cls._events.append(event)

        # Best-effort DB write — never raises even if _persist_to_db raises
        try:
            cls._persist_to_db(event_type, details)
        except Exception:
            pass

        return event

    @classmethod
    def _persist_to_db(cls, event_type: str, details: str) -> None:
        """Write audit event to system_logs table. Silently handles all errors."""
        try:
            from app.core.database import SessionLocal
            from app.models.models import SystemLog
            db = SessionLocal()
            try:
                log = SystemLog(
                    level="AUDIT",
                    module=f"LIVE_PAPER/{event_type}",
                    message=details[:2000],  # Truncate to fit column
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception:
            pass  # DB write failures must never interrupt live trading

    @classmethod
    def get_events(cls, limit: int = 50) -> List[LiveAuditEvent]:
        return cls._events[-limit:]

    @classmethod
    def clear(cls):
        cls._events.clear()
        cls._event_counter = 0
