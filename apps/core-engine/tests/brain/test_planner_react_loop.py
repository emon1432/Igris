"""Tests for TaskOrchestrator ReAct Loop."""

import pytest
from igris.action.mouse_keyboard import InputDriver
from igris.action.virtual_display import VirtualDisplayManager
from igris.brain.dispatcher import ActionDispatcher
from igris.brain.planner import TaskOrchestrator
from igris.brain.vlm_client import VisualAction, VLMClient
from igris.core.state import ExecutionMode
from igris.perception.resolver import CoordinateResolver
from igris.perception.screen import ScreenCaptureEngine


class MockVLMClient(VLMClient):
    """Simulates a multi-step autonomous decision sequence without calling external APIs."""

    def __init__(self, step_actions):
        super().__init__(api_key="mock")
        self.step_actions = step_actions
        self.call_count = 0

    def predict_action(self, frame, task_goal, recent_history=None):
        if self.call_count < len(self.step_actions):
            action = self.step_actions[self.call_count]
        else:
            action = VisualAction(action_type="finished", task_completed=True, reasoning="Finished default")
        self.call_count += 1
        return action


@pytest.fixture(scope="module")
def planner_display():
    """Start isolated virtual display."""
    display = VirtualDisplayManager.find_free_display(start=91)
    mgr = VirtualDisplayManager(display=display, width=1920, height=1080)
    mgr.start(timeout_seconds=5.0)
    yield display
    mgr.stop()


@pytest.mark.asyncio
async def test_orchestrator_multi_step_react_loop(planner_display):
    """Verify autonomous ReAct loop executing through Observe -> Reason -> Act -> Verify until completion."""
    simulated_steps = [
        VisualAction(action_type="click", normalized_x=200, normalized_y=300, reasoning="Click search bar"),
        VisualAction(action_type="type", text_input="Naeem", reasoning="Type recipient name"),
        VisualAction(action_type="finished", task_completed=True, reasoning="Message sent successfully"),
    ]

    mock_vlm = MockVLMClient(step_actions=simulated_steps)
    screen_eng = ScreenCaptureEngine(default_display=planner_display)
    input_drv = InputDriver(default_display=planner_display)
    dispatcher = ActionDispatcher(input_driver=input_drv, coordinate_resolver=CoordinateResolver())

    orchestrator = TaskOrchestrator(
        vlm_client=mock_vlm,
        screen_engine=screen_eng,
        dispatcher=dispatcher,
        max_iterations=10,
        verification_delay=0.1,  # Fast verification for test
    )

    summary = await orchestrator.execute_task(
        task_goal="Send message to Naeem",
        mode=ExecutionMode.GHOST,
        target_display=planner_display,
    )

    assert summary.success
    assert summary.total_steps == 3
    assert "Message sent successfully" in summary.final_message
    assert len(summary.history) == 3
    assert summary.history[0].action_type == "click"
    assert summary.history[1].action_type == "type"
    assert summary.history[2].action_type == "finished"

