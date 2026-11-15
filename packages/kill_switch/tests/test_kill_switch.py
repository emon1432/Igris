"""Unit Tests for Kill Switch Subsystem."""

import pytest
from igris_kill_switch.manager import KillSwitchManager, KillSwitchEngagedError


def test_kill_switch_lifecycle():
    ks = KillSwitchManager()
    assert ks.is_engaged is False

    ks.register_task("task_001")
    ks.register_token("token_001", {"tier": "T2"})

    # Trigger kill switch
    event = ks.trigger(source="WEB_BUTTON", reason="User emergency stop")
    assert ks.is_engaged is True
    assert "task_001" in event["terminated_tasks"]
    assert "token_001" in event["revoked_tokens"]

    # Health check must raise
    with pytest.raises(KillSwitchEngagedError):
        ks.assert_healthy()

    with pytest.raises(KillSwitchEngagedError):
        ks.register_task("task_002")


def test_kill_switch_callbacks():
    ks = KillSwitchManager()
    called = []

    def on_kill(source, reason):
        called.append((source, reason))

    ks.register_callback(on_kill)
    ks.trigger(source="CLI", reason="Keyboard interrupt")

    assert len(called) == 1
    assert called[0] == ("CLI", "Keyboard interrupt")

