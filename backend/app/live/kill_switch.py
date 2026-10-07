"""
Hierarchical Kill Switch — Phase 7
5-level escalating intervention system for live paper trading safety.

Level 1: Pause signal generation only
Level 2: No new entries (manage existing exits only)
Level 3: Close all open positions immediately
Level 4: Freeze all activity + emit alert
Level 5: Full system halt — requires manual reset

PAPER TRADING ONLY — Does not touch real broker orders.
"""
import datetime
from typing import Dict, Any, Optional
from enum import IntEnum


class KillSwitchLevel(IntEnum):
    """Kill switch escalation levels. Higher = more severe."""
    NONE = 0
    L1_PAUSE_SIGNALS = 1
    L2_NO_NEW_ENTRIES = 2
    L3_CLOSE_ALL_POSITIONS = 3
    L4_FREEZE_ALL = 4
    L5_FULL_HALT = 5


class HierarchicalKillSwitch:
    """
    5-level hierarchical kill switch for live paper trading safety.

    Escalation is cumulative: Level N includes all restrictions of Levels < N.
    Level 5 requires manual reset before any trading activity can resume.
    """

    def __init__(self):
        self._current_level: KillSwitchLevel = KillSwitchLevel.NONE
        self._activation_reason: Optional[str] = None
        self._activation_time: Optional[datetime.datetime] = None
        self._level_5_manual_reset_required: bool = False
        self._activation_log: list = []

    @property
    def current_level(self) -> KillSwitchLevel:
        return self._current_level

    @property
    def is_active(self) -> bool:
        return self._current_level > KillSwitchLevel.NONE

    @property
    def requires_manual_reset(self) -> bool:
        return self._level_5_manual_reset_required

    @property
    def activation_reason(self) -> Optional[str]:
        return self._activation_reason

    # ── Level checks (cumulative) ─────────────────────────────────────────────

    def can_generate_signals(self) -> bool:
        """Level 1+ blocks signal generation."""
        return self._current_level < KillSwitchLevel.L1_PAUSE_SIGNALS

    def can_open_new_positions(self) -> bool:
        """Level 2+ blocks new position entries."""
        return self._current_level < KillSwitchLevel.L2_NO_NEW_ENTRIES

    def is_frozen(self) -> bool:
        """Level 4+ freezes all activity."""
        return self._current_level >= KillSwitchLevel.L4_FREEZE_ALL

    def is_halted(self) -> bool:
        """Level 5 — full system halt."""
        return self._current_level >= KillSwitchLevel.L5_FULL_HALT

    # ── Activation ────────────────────────────────────────────────────────────

    def activate(
        self,
        level: KillSwitchLevel,
        reason: str,
        triggered_by: str = "SYSTEM"
    ) -> Dict[str, Any]:
        """
        Activate the kill switch at the given level.
        Level cannot be reduced via activate() — use reset() to deescalate.
        """
        if self._level_5_manual_reset_required:
            return {
                "success": False,
                "error": "LEVEL 5 ACTIVE — Manual reset required before any state change.",
                "current_level": int(self._current_level)
            }

        # Only escalate, never auto-deescalate
        new_level = max(self._current_level, level)
        self._current_level = new_level
        self._activation_reason = reason
        self._activation_time = datetime.datetime.now()

        if new_level == KillSwitchLevel.L5_FULL_HALT:
            self._level_5_manual_reset_required = True

        event = {
            "timestamp": self._activation_time.isoformat(),
            "level": int(new_level),
            "level_name": new_level.name,
            "reason": reason,
            "triggered_by": triggered_by
        }
        self._activation_log.append(event)

        return {
            "success": True,
            "current_level": int(new_level),
            "level_name": new_level.name,
            "reason": reason,
            "restrictions": self._describe_restrictions(new_level),
            "manual_reset_required": self._level_5_manual_reset_required
        }

    def activate_level1(self, reason: str = "Pause signal generation") -> Dict[str, Any]:
        return self.activate(KillSwitchLevel.L1_PAUSE_SIGNALS, reason)

    def activate_level2(self, reason: str = "No new entries") -> Dict[str, Any]:
        return self.activate(KillSwitchLevel.L2_NO_NEW_ENTRIES, reason)

    def activate_level3(self, reason: str = "Emergency stop — close all positions") -> Dict[str, Any]:
        return self.activate(KillSwitchLevel.L3_CLOSE_ALL_POSITIONS, reason)

    def activate_level4(self, reason: str = "Full activity freeze") -> Dict[str, Any]:
        return self.activate(KillSwitchLevel.L4_FREEZE_ALL, reason)

    def activate_level5(self, reason: str = "FULL SYSTEM HALT — manual reset required") -> Dict[str, Any]:
        return self.activate(KillSwitchLevel.L5_FULL_HALT, reason)

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self, manual_operator_code: str = "") -> Dict[str, Any]:
        """
        Deescalate kill switch.
        Level 5 requires manual_operator_code = 'CONFIRM_MANUAL_RESET' to proceed.
        """
        if self._level_5_manual_reset_required:
            if manual_operator_code != "CONFIRM_MANUAL_RESET":
                return {
                    "success": False,
                    "error": "Level 5 is active. Provide manual_operator_code='CONFIRM_MANUAL_RESET' to reset.",
                    "current_level": int(self._current_level)
                }
            self._level_5_manual_reset_required = False

        prev_level = self._current_level
        self._current_level = KillSwitchLevel.NONE
        self._activation_reason = None

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event": "RESET",
            "from_level": int(prev_level),
            "to_level": 0
        }
        self._activation_log.append(event)

        return {
            "success": True,
            "previous_level": int(prev_level),
            "current_level": 0,
            "message": "Kill switch reset. System operational."
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_level": int(self._current_level),
            "level_name": self._current_level.name,
            "is_active": self.is_active,
            "activation_reason": self._activation_reason,
            "activation_time": self._activation_time.isoformat() if self._activation_time else None,
            "manual_reset_required": self._level_5_manual_reset_required,
            "restrictions": self._describe_restrictions(self._current_level),
            "can_generate_signals": self.can_generate_signals(),
            "can_open_new_positions": self.can_open_new_positions(),
            "is_frozen": self.is_frozen(),
            "is_halted": self.is_halted()
        }

    def get_log(self) -> list:
        return self._activation_log.copy()

    @staticmethod
    def _describe_restrictions(level: KillSwitchLevel) -> list:
        restrictions = []
        if level >= KillSwitchLevel.L1_PAUSE_SIGNALS:
            restrictions.append("Signal generation PAUSED")
        if level >= KillSwitchLevel.L2_NO_NEW_ENTRIES:
            restrictions.append("New position entries BLOCKED")
        if level >= KillSwitchLevel.L3_CLOSE_ALL_POSITIONS:
            restrictions.append("All open positions CLOSING")
        if level >= KillSwitchLevel.L4_FREEZE_ALL:
            restrictions.append("All activity FROZEN — alerts active")
        if level >= KillSwitchLevel.L5_FULL_HALT:
            restrictions.append("FULL SYSTEM HALT — manual reset required")
        return restrictions
