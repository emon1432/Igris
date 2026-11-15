"""Evaluation Case K-01: Universal Kill Switch Verification.

Evaluation Objective:
Verify that triggering the emergency kill switch halts all active orchestrator tasks,
terminates subagents and child processes, revokes in-flight approval tokens,
and blocks subsequent tool execution deterministically.
"""

import pytest
from igris_kill_switch.manager import KillSwitchManager, KillSwitchEngagedError


def test_k01_kill_switch_clears_tasks_and_tokens():
    """Kill switch activation must purge active tasks and approval tokens."""
    manager = KillSwitchManager()
    assert manager.is_engaged is False

    manager.register_task("task_101", {"type": "code_refactor"})
    manager.register_task("task_102", {"type": "email_triage"})
    manager.register_token("token_abc", {"tier": "T2"})
    manager.register_token("token_xyz", {"tier": "T3"})

    event = manager.trigger(source="WEB_UI_BUTTON", reason="Emergency operator interrupt")
    assert manager.is_engaged is True
    assert event["status"] == "KILL_SWITCH_ENGAGED"
    assert "task_101" in event["terminated_tasks"]
    assert "task_102" in event["terminated_tasks"]
    assert "token_abc" in event["revoked_tokens"]
    assert "token_xyz" in event["revoked_tokens"]


def test_k01_actions_blocked_after_kill_switch():
    """Subsequent operations must raise KillSwitchEngagedError when kill switch is active."""
    manager = KillSwitchManager()
    manager.trigger(source="CLI_SIGNAL", reason="Fatal boundary breach")

    with pytest.raises(KillSwitchEngagedError) as exc_info:
        manager.assert_healthy()

    assert "Emergency Kill Switch is ENGAGED" in str(exc_info.value)
