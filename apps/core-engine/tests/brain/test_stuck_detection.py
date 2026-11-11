"""Tests for stuck detection in TaskOrchestrator."""

from igris.brain.planner import TaskOrchestrator
from igris.core.state import TaskStepRecord


def test_stuck_detector_identifies_loop():
    """Verify stuck detector catches 3 consecutive clicks at identical coordinates."""
    orchestrator = TaskOrchestrator()

    history = [
        TaskStepRecord(step_number=1, action_type="click", reasoning="Click 1", target_coordinate=(450, 320)),
        TaskStepRecord(step_number=2, action_type="click", reasoning="Click 2", target_coordinate=(450, 321)),
        TaskStepRecord(step_number=3, action_type="click", reasoning="Click 3", target_coordinate=(451, 320)),
    ]

    assert orchestrator._is_stuck(history)


def test_stuck_detector_ignores_moving_actions():
    """Verify stuck detector does not trigger if coordinates or action types change."""
    orchestrator = TaskOrchestrator()

    history = [
        TaskStepRecord(step_number=1, action_type="click", reasoning="Click 1", target_coordinate=(100, 100)),
        TaskStepRecord(step_number=2, action_type="click", reasoning="Click 2", target_coordinate=(200, 200)),
        TaskStepRecord(step_number=3, action_type="type", reasoning="Type 3", target_coordinate=None),
    ]

    assert not orchestrator._is_stuck(history)

