"""
Phase 8 — Data Quality Monitor
Tracks real-time data feed health metrics per symbol and per provider.
Used by the quality gate and dashboard to show provider reliability.
"""
import datetime
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SymbolQualityStats:
    symbol: str
    tick_count: int = 0
    invalid_tick_count: int = 0
    duplicate_count: int = 0
    reconnect_count: int = 0
    latency_samples_ms: List[float] = field(default_factory=list)
    last_tick_at: Optional[datetime.datetime] = None
    session_start: datetime.datetime = field(default_factory=datetime.datetime.now)

    @property
    def avg_latency_ms(self) -> float:
        if not self.latency_samples_ms:
            return 0.0
        return round(sum(self.latency_samples_ms) / len(self.latency_samples_ms), 1)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latency_samples_ms:
            return 0.0
        sorted_samples = sorted(self.latency_samples_ms)
        idx = int(len(sorted_samples) * 0.95)
        return round(sorted_samples[min(idx, len(sorted_samples) - 1)], 1)

    @property
    def max_latency_ms(self) -> float:
        return round(max(self.latency_samples_ms), 1) if self.latency_samples_ms else 0.0

    @property
    def invalid_rate_pct(self) -> float:
        if self.tick_count == 0:
            return 0.0
        return round(self.invalid_tick_count / self.tick_count * 100.0, 2)

    @property
    def ticks_per_minute(self) -> float:
        elapsed = (datetime.datetime.now() - self.session_start).total_seconds()
        if elapsed < 1:
            return 0.0
        return round(self.tick_count / (elapsed / 60.0), 1)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "tick_count": self.tick_count,
            "invalid_tick_count": self.invalid_tick_count,
            "duplicate_count": self.duplicate_count,
            "reconnect_count": self.reconnect_count,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "invalid_rate_pct": self.invalid_rate_pct,
            "ticks_per_minute": self.ticks_per_minute,
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at else None,
        }


class Phase8DataQualityMonitor:
    """
    Real-time data quality tracking for Phase 8.
    Thread-safe counters for latency, drops, reconnects and validation stats.
    Used by the /api/live/data-quality endpoint and the /live dashboard.
    """

    # Alert thresholds (configurable)
    LATENCY_WARN_MS = 200.0          # Warn if avg latency > 200ms
    LATENCY_CRITICAL_MS = 1000.0     # Critical if avg latency > 1s
    INVALID_RATE_WARN_PCT = 5.0      # Warn if > 5% ticks invalid
    MAX_LATENCY_SAMPLES = 500        # Keep last 500 samples per symbol

    def __init__(self):
        self._stats: Dict[str, SymbolQualityStats] = {}
        self._provider_reconnects: int = 0
        self._provider_errors: int = 0
        self._session_start: datetime.datetime = datetime.datetime.now()
        self._lock = threading.Lock()

    def record_tick(self, symbol: str, latency_ms: float, is_valid: bool, is_duplicate: bool = False):
        """Called for every tick received (valid or not)."""
        with self._lock:
            if symbol not in self._stats:
                self._stats[symbol] = SymbolQualityStats(symbol=symbol)
            s = self._stats[symbol]
            s.tick_count += 1
            s.last_tick_at = datetime.datetime.now()
            if not is_valid:
                s.invalid_tick_count += 1
            if is_duplicate:
                s.duplicate_count += 1
            # Keep bounded latency sample window
            s.latency_samples_ms.append(latency_ms)
            if len(s.latency_samples_ms) > self.MAX_LATENCY_SAMPLES:
                s.latency_samples_ms.pop(0)

    def record_reconnect(self, symbol: Optional[str] = None):
        """Record a provider reconnect event."""
        with self._lock:
            self._provider_reconnects += 1
            if symbol and symbol in self._stats:
                self._stats[symbol].reconnect_count += 1

    def record_provider_error(self):
        """Record a provider-level error."""
        with self._lock:
            self._provider_errors += 1

    def get_symbol_stats(self, symbol: str) -> Optional[dict]:
        with self._lock:
            s = self._stats.get(symbol)
            return s.to_dict() if s else None

    def get_all_symbol_stats(self) -> List[dict]:
        with self._lock:
            return [s.to_dict() for s in self._stats.values()]

    def get_provider_summary(self) -> dict:
        """Overall provider health summary."""
        with self._lock:
            total_ticks = sum(s.tick_count for s in self._stats.values())
            total_invalid = sum(s.invalid_tick_count for s in self._stats.values())
            all_latencies = []
            for s in self._stats.values():
                all_latencies.extend(s.latency_samples_ms)

            avg_latency = (
                round(sum(all_latencies) / len(all_latencies), 1)
                if all_latencies else 0.0
            )
            uptime_pct = self._calculate_uptime()

            alerts = []
            if avg_latency > self.LATENCY_CRITICAL_MS:
                alerts.append(f"CRITICAL: Average latency {avg_latency}ms exceeds {self.LATENCY_CRITICAL_MS}ms")
            elif avg_latency > self.LATENCY_WARN_MS:
                alerts.append(f"WARNING: Average latency {avg_latency}ms exceeds {self.LATENCY_WARN_MS}ms")

            invalid_rate = (total_invalid / total_ticks * 100.0) if total_ticks > 0 else 0.0
            if invalid_rate > self.INVALID_RATE_WARN_PCT:
                alerts.append(f"WARNING: {invalid_rate:.1f}% ticks invalid (threshold {self.INVALID_RATE_WARN_PCT}%)")

            return {
                "total_ticks": total_ticks,
                "total_invalid": total_invalid,
                "invalid_rate_pct": round(invalid_rate, 2),
                "avg_latency_ms": avg_latency,
                "provider_reconnects": self._provider_reconnects,
                "provider_errors": self._provider_errors,
                "uptime_pct": uptime_pct,
                "symbols_tracked": len(self._stats),
                "session_start": self._session_start.isoformat(),
                "quality_alerts": alerts,
                "quality_status": "DEGRADED" if alerts else "HEALTHY"
            }

    def _calculate_uptime(self) -> float:
        """Estimate uptime based on reconnect count (simple heuristic)."""
        elapsed_minutes = (datetime.datetime.now() - self._session_start).total_seconds() / 60.0
        if elapsed_minutes < 1:
            return 100.0
        # Assume each reconnect costs ~1 minute of downtime
        down_minutes = min(self._provider_reconnects, elapsed_minutes)
        return round(max(0.0, (elapsed_minutes - down_minutes) / elapsed_minutes * 100.0), 1)

    def reset(self):
        """Reset all stats for a new session."""
        with self._lock:
            self._stats.clear()
            self._provider_reconnects = 0
            self._provider_errors = 0
            self._session_start = datetime.datetime.now()
