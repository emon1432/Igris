"""Evaluation Case K-01: Universal Kill Switch Verification.

Evaluation Objective:
Verify that triggering the emergency kill switch halts all active orchestrator tasks,
terminates subagents and child processes, revokes in-flight approval tokens,
and appends a critical audit entry into the immutable ledger.
"""

import pytest
from typing import Dict, Any, List


class MockKillSwitchManager:
    """Contract specification for the Kill Switch subsystem."""

    def __init__(self):
        self.is_active = False
        self.active_tasks = ["task_101", "task_102"]
        self.valid_approval_tokens = ["token_abc", "token_xyz"]
        self.ledger_events: List[Dict[str, Any]] = []

    def trigger(self, trigger_source: str) -> Dict[str, Any]:
        self.is_active = True
        killed_tasks = list(self.active_tasks)
        self.active_tasks.clear()
        revoked_tokens = list(self.valid_approval_tokens)
        self.valid_approval_tokens.clear()

        event = {
            "event": "KILL_SWITCH_ENGAGED",
            "source": trigger_source,
            "killed_tasks": killed_tasks,
            "revoked_tokens": revoked_tokens,
        }
        self.ledger_events.append(event)
        return event

    def can_dispatch_action(self, task_id: str, token_id: str) -> bool:
        if self.is_active:
            return False
        return task_id in self.active_tasks and token_id in self.valid_approval_tokens


def test_k01_kill_switch_clears_tasks_and_tokens():
    """Kill switch activation must purge active tasks and approval tokens."""
    manager = MockKillSwitchManager()
    assert len(manager.active_tasks) == 2
    assert len(manager.valid_approval_tokens) == 2

    event = manager.trigger(trigger_source="WEB_UI_BUTTON")
    assert manager.is_active is True
    assert len(manager.active_tasks) == 0
    assert len(manager.valid_approval_tokens) == 0
    assert event["event"] == "KILL_SWITCH_ENGAGED"


def test_k01_actions_blocked_after_kill_switch():
    """Subsequent action dispatch must fail when kill switch is engaged."""
    manager = MockKillSwitchManager()
    manager.trigger(trigger_source="CLI_SIGNAL")

    can_dispatch = manager.can_dispatch_action("task_101", "token_abc")
    assert can_dispatch is False
