"""
Tests for Phase 7 Hierarchical Kill Switch
Covers all 5 levels, cumulative restrictions, Level 5 manual reset, and escalation rule.
"""
import pytest
from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel


class TestLevel1PauseSignals:
    def test_level1_blocks_signals(self):
        ks = HierarchicalKillSwitch()
        result = ks.activate_level1("Test pause")
        assert result["success"] is True
        assert ks.can_generate_signals() is False
        assert ks.can_open_new_positions() is True  # Not yet restricted

    def test_level1_description(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level1()
        assert "Signal generation PAUSED" in ks.get_status()["restrictions"]


class TestLevel2NoNewEntries:
    def test_level2_blocks_entries_and_signals(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level2("Block new entries")
        assert ks.can_generate_signals() is False
        assert ks.can_open_new_positions() is False
        assert ks.is_frozen() is False  # Level 4 not yet reached


class TestLevel3CloseAll:
    def test_level3_includes_l1_and_l2_restrictions(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level3()
        assert ks.can_generate_signals() is False
        assert ks.can_open_new_positions() is False

    def test_level3_status_shows_closing(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level3("Emergency")
        restrictions = ks.get_status()["restrictions"]
        assert "All open positions CLOSING" in restrictions


class TestLevel4Freeze:
    def test_level4_is_frozen(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level4("Freeze all")
        assert ks.is_frozen() is True
        assert ks.is_halted() is False


class TestLevel5FullHalt:
    def test_level5_halts_system(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level5("Critical failure")
        assert ks.is_halted() is True
        assert ks.requires_manual_reset is True

    def test_level5_blocks_further_activation_without_reset(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level5("Critical")
        result = ks.activate_level1("Try again")
        assert result["success"] is False
        assert "Manual reset required" in result["error"]

    def test_level5_reset_without_code_fails(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level5("Critical")
        result = ks.reset()
        assert result["success"] is False

    def test_level5_reset_with_correct_code_succeeds(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level5("Critical")
        result = ks.reset("CONFIRM_MANUAL_RESET")
        assert result["success"] is True
        assert ks.current_level == KillSwitchLevel.NONE
        assert ks.requires_manual_reset is False


class TestEscalationRules:
    def test_cannot_deescalate_via_activate(self):
        """Activating a lower level while higher is active must not reduce level."""
        ks = HierarchicalKillSwitch()
        ks.activate_level3("Emergency")
        ks.activate_level1("Try to reduce")  # Should stay at L3
        assert ks.current_level == KillSwitchLevel.L3_CLOSE_ALL_POSITIONS

    def test_escalation_always_goes_up(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level2()
        ks.activate_level4()
        assert ks.current_level == KillSwitchLevel.L4_FREEZE_ALL


class TestStatusAndLog:
    def test_status_includes_restrictions(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level2()
        status = ks.get_status()
        assert "current_level" in status
        assert "level_name" in status
        assert "is_active" in status
        assert status["is_active"] is True

    def test_log_records_events(self):
        ks = HierarchicalKillSwitch()
        ks.activate_level1("First")
        ks.activate_level3("Third")
        log = ks.get_log()
        assert len(log) == 2
        assert log[0]["level"] == 1
        assert log[1]["level"] == 3

    def test_inactive_switch_allows_all(self):
        ks = HierarchicalKillSwitch()
        assert ks.can_generate_signals() is True
        assert ks.can_open_new_positions() is True
        assert ks.is_frozen() is False
        assert ks.is_halted() is False
        assert ks.is_active is False
