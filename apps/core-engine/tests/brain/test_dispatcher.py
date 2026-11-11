"""Tests for ActionDispatcher."""

import pytest
from igris.action.mouse_keyboard import InputDriver
from igris.action.virtual_display import VirtualDisplayManager
from igris.brain.dispatcher import ActionDispatcher
from igris.brain.vlm_client import VisualAction
from igris.perception.resolver import CoordinateResolver


@pytest.fixture(scope="module")
def test_display():
    """Start an isolated virtual display for dispatcher testing."""
    display = VirtualDisplayManager.find_free_display(start=92)
    mgr = VirtualDisplayManager(display=display, width=1920, height=1080)
    mgr.start(timeout_seconds=5.0)
    yield display
    mgr.stop()


@pytest.mark.asyncio
async def test_dispatcher_actions(test_display):
    """Verify dispatching various VisualAction types on a virtual display."""
    input_drv = InputDriver(default_display=test_display)
    resolver = CoordinateResolver()
    dispatcher = ActionDispatcher(input_driver=input_drv, coordinate_resolver=resolver)

    # 1. Click action
    act_click = VisualAction(action_type="click", normalized_x=500, normalized_y=500, reasoning="Click center")
    res1 = await dispatcher.dispatch(act_click, 1920, 1080, test_display)
    assert res1.success
    assert "Clicked at (960, 540)" in res1.details

    # 2. Type action
    act_type = VisualAction(action_type="type", text_input="Test Input", reasoning="Enter text")
    res2 = await dispatcher.dispatch(act_type, 1920, 1080, test_display)
    assert res2.success
    assert "Typed text" in res2.details

    # 3. Wait action
    act_wait = VisualAction(action_type="wait", reasoning="Wait for modal")
    res3 = await dispatcher.dispatch(act_wait, 1920, 1080, test_display)
    assert res3.success

    # 4. Finished action
    act_finish = VisualAction(action_type="finished", task_completed=True, reasoning="Goal done")
    res4 = await dispatcher.dispatch(act_finish, 1920, 1080, test_display)
    assert res4.success
    assert "Task completed" in res4.details

