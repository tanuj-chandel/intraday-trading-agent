"""
Phase 8 — Alert Engine
Internal alerting for system health, data quality, and trading safety events.
Alerts are stored in-memory (ring buffer) and persisted to system_logs DB table.
Alerts NEVER bypass safety controls — they are notifications only.
"""
import datetime
import threading
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from collections import deque


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    DATA_DISCONNECT = "DATA_DISCONNECT"
    STALE_DATA = "STALE_DATA"
    HIGH_LATENCY = "HIGH_LATENCY"
    REPEATED_API_ERROR = "REPEATED_API_ERROR"
    EXCESSIVE_SLIPPAGE = "EXCESSIVE_SLIPPAGE"
    DAILY_LOSS_THRESHOLD = "DAILY_LOSS_THRESHOLD"
    CONSECUTIVE_LOSSES = "CONSECUTIVE_LOSSES"
    STRATEGY_DEGRADATION = "STRATEGY_DEGRADATION"
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"
    SQUARE_OFF_FAILED = "SQUARE_OFF_FAILED"
    RECOVERY_FAILED = "RECOVERY_FAILED"
    INVALID_TICK_RATE = "INVALID_TICK_RATE"
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    SIGNAL_BLOCKED = "SIGNAL_BLOCKED"
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"


@dataclass
class Alert:
    id: int
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    symbol: Optional[str] = None
    resolved: bool = False
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    resolved_at: Optional[datetime.datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "symbol": self.symbol,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }


class Phase8AlertEngine:
    """
    Internal alerting for Phase 8.
    Fires alerts for data quality, risk, and operational events.
    
    Alerts are INFORMATIONAL — they never bypass kill switch or risk manager.
    Safety controls remain independent.
    """

    MAX_ALERTS = 500  # In-memory ring buffer

    def __init__(self):
        self._alerts: deque = deque(maxlen=self.MAX_ALERTS)
        self._counter: int = 0
        self._lock = threading.Lock()
        # Dedup: don't fire same alert type for same symbol within cooldown
        self._last_fired: Dict[str, datetime.datetime] = {}
        self.DEDUP_COOLDOWN_SECONDS = 60  # 1 minute cooldown for same alert type

    def fire(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        symbol: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        bypass_dedup: bool = False
    ) -> Optional[Alert]:
        """
        Fire an alert. Returns the Alert object or None if deduped.
        Persists to DB best-effort.
        """
        dedup_key = f"{alert_type.value}:{symbol or '_GLOBAL_'}"
        now = datetime.datetime.now()

        with self._lock:
            if not bypass_dedup:
                last = self._last_fired.get(dedup_key)
                if last and (now - last).total_seconds() < self.DEDUP_COOLDOWN_SECONDS:
                    return None  # Suppressed duplicate

            self._counter += 1
            alert = Alert(
                id=self._counter,
                alert_type=alert_type,
                severity=severity,
                message=message,
                symbol=symbol,
                metadata=metadata or {},
                created_at=now
            )
            self._alerts.append(alert)
            self._last_fired[dedup_key] = now

        # Best-effort DB persist — never block trading on DB failure
        try:
            self._persist_to_db(alert)
        except Exception:
            pass
        return alert

    def resolve(self, alert_id: int):
        """Mark an alert as resolved."""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.datetime.now()
                    break

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[dict]:
        """Get unresolved alerts, optionally filtered by severity."""
        with self._lock:
            alerts = [a for a in self._alerts if not a.resolved]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            return [a.to_dict() for a in reversed(list(alerts))]

    def get_all_alerts(self, limit: int = 100) -> List[dict]:
        """Get all alerts (resolved and active) most-recent first."""
        with self._lock:
            all_list = list(self._alerts)
            return [a.to_dict() for a in reversed(all_list[-limit:])]

    def get_summary(self) -> dict:
        """Summary count by severity."""
        with self._lock:
            active = [a for a in self._alerts if not a.resolved]
            return {
                "total_alerts": len(self._alerts),
                "active_alerts": len(active),
                "critical_active": sum(1 for a in active if a.severity == AlertSeverity.CRITICAL),
                "warning_active": sum(1 for a in active if a.severity == AlertSeverity.WARNING),
                "info_active": sum(1 for a in active if a.severity == AlertSeverity.INFO),
            }

    def _persist_to_db(self, alert: Alert):
        """Write alert to system_logs table. Never raises — best effort only."""
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                from app.models.models import SystemLog
                log = SystemLog(
                    timestamp=alert.created_at,
                    level=alert.severity.value,
                    module=f"ALERT:{alert.alert_type.value}",
                    message=alert.message,
                    details={
                        "symbol": alert.symbol,
                        "alert_type": alert.alert_type.value,
                        "severity": alert.severity.value,
                        "metadata": alert.metadata,
                    }
                )
                db.add(log)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass  # Never block trading for a failed log write

    # ── Convenience fire methods ──────────────────────────────────────────────

    def data_disconnect(self, provider: str, reason: str):
        return self.fire(AlertType.DATA_DISCONNECT, AlertSeverity.CRITICAL,
                         f"Data feed DISCONNECTED: {provider} — {reason}")

    def stale_data(self, symbol: str, age_seconds: float):
        return self.fire(AlertType.STALE_DATA, AlertSeverity.WARNING,
                         f"Stale data for {symbol}: {age_seconds:.0f}s old", symbol=symbol)

    def high_latency(self, provider: str, latency_ms: float):
        severity = AlertSeverity.CRITICAL if latency_ms > 1000 else AlertSeverity.WARNING
        return self.fire(AlertType.HIGH_LATENCY, severity,
                         f"High data latency from {provider}: {latency_ms:.0f}ms")

    def consecutive_losses(self, count: int):
        severity = AlertSeverity.CRITICAL if count >= 5 else AlertSeverity.WARNING
        return self.fire(AlertType.CONSECUTIVE_LOSSES, severity,
                         f"Consecutive paper trading losses: {count}",
                         bypass_dedup=(count >= 5))

    def daily_loss_threshold(self, loss_amount: float, threshold: float):
        return self.fire(AlertType.DAILY_LOSS_THRESHOLD, AlertSeverity.CRITICAL,
                         f"Daily loss ₹{loss_amount:.0f} approaching limit ₹{threshold:.0f}")

    def excessive_slippage(self, symbol: str, slippage_pct: float):
        return self.fire(AlertType.EXCESSIVE_SLIPPAGE, AlertSeverity.WARNING,
                         f"Excessive slippage for {symbol}: {slippage_pct*100:.2f}%", symbol=symbol)

    def strategy_degradation(self, verdict: str, breaches: list):
        return self.fire(AlertType.STRATEGY_DEGRADATION, AlertSeverity.CRITICAL,
                         f"Strategy degradation detected: {verdict}. Breaches: {', '.join(breaches)}",
                         bypass_dedup=True)

    def kill_switch_activated(self, level: int, reason: str):
        return self.fire(AlertType.KILL_SWITCH_ACTIVATED, AlertSeverity.CRITICAL,
                         f"Kill Switch Level {level} activated: {reason}", bypass_dedup=True)

    def missing_credentials(self, provider: str):
        return self.fire(AlertType.MISSING_CREDENTIALS, AlertSeverity.INFO,
                         f"No API credentials configured for {provider}. System in UNCONFIGURED state.")

    def invalid_tick_rate(self, symbol: str, rate_pct: float):
        return self.fire(AlertType.INVALID_TICK_RATE, AlertSeverity.WARNING,
                         f"High invalid tick rate for {symbol}: {rate_pct:.1f}%", symbol=symbol)


# Global singleton
alert_engine = Phase8AlertEngine()
