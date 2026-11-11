"""Tests for SafetyInterlockListener."""

from igris.action.safety_interlock import SafetyInterlockListener


def test_safety_interlock_manual_trigger():
    """Verify emergency trigger and callback invocation."""
    callback_called = False

    def on_override():
        nonlocal callback_called
        callback_called = True

    listener = SafetyInterlockListener(
        mouse_threshold_px=10,
        emergency_keys=["Escape"],
        on_override_callback=on_override,
    )

    assert not listener.is_triggered
    assert not callback_called

    # Simulate trigger
    listener._trigger_override("Test simulated override")
    assert listener.is_triggered
    assert callback_called

    # Reset
    listener.reset()
    assert not listener.is_triggered


def test_safety_interlock_agent_notification():
    """Verify that expected agent moves update state."""
    listener = SafetyInterlockListener(mouse_threshold_px=10)
    listener.notify_agent_move(500, 400)
    assert listener._expected_cursor_pos == (500, 400)
    assert listener._last_cursor_pos == (500, 400)
