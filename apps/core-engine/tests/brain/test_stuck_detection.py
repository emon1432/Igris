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


def test_tab_storm_detector_blocks_repetitive_browser_tabs():
    """Verify tab storm detector catches multiple browser or tab-opening actions."""
    from igris.brain.vlm_client import VisualAction

    orchestrator = TaskOrchestrator()

    # Past step already opened a browser or tab
    history = [
        TaskStepRecord(step_number=1, action_type="hotkey", reasoning="Open browser tab", details="ctrl+t"),
    ]

    # Current action attempts to open yet another tab
    action = VisualAction(
        action_type="hotkey",
        text_input="ctrl+t",
        reasoning="Open another tab",
    )

    assert orchestrator._detect_tab_storm(history, action) is True

    # But non-tab actions (like reading, typing, clicking result) are allowed
    normal_action = VisualAction(
        action_type="click",
        normalized_x=500,
        normalized_y=400,
        reasoning="Click search result link",
    )
    assert orchestrator._detect_tab_storm(history, normal_action) is False


def test_tab_storm_detector_blocks_terminal_browser_loop():
    """Verify tab storm detector catches terminal google-chrome repeated actions."""
    from igris.brain.vlm_client import VisualAction

    orchestrator = TaskOrchestrator()

    # Step 1 launched Chrome
    history = [
        TaskStepRecord(
            step_number=1,
            action_type="terminal",
            reasoning="Launch Google Chrome to search",
            details="Ran shell command 'google-chrome https://google.com' (code 0)",
        ),
    ]

    # Step 2 attempts to launch Chrome again via terminal (the 25-tab bug scenario)
    action = VisualAction(
        action_type="terminal",
        text_input="google-chrome https://google.com/search?q=salam+dao &",
        reasoning="The screen is black, so I am launching Google Chrome to search for 'salam dao'",
    )

    assert orchestrator._detect_tab_storm(history, action) is True


def test_stuck_detector_catches_repeated_terminal_commands():
    """Verify stuck detector catches 2 consecutive terminal actions."""
    orchestrator = TaskOrchestrator()

    history = [
        TaskStepRecord(step_number=1, action_type="terminal", reasoning="Run cmd 1", details="cmd 1"),
        TaskStepRecord(step_number=2, action_type="terminal", reasoning="Run cmd 2", details="cmd 2"),
    ]

    assert orchestrator._is_stuck(history) is True


