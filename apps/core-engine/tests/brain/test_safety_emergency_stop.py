"""Tests for Safety Interlock halt during ReAct loop."""

import asyncio
import pytest
from igris.action.safety_interlock import SafetyInterlockListener
from igris.action.virtual_display import VirtualDisplayManager
from igris.brain.planner import TaskOrchestrator
from igris.brain.vlm_client import VisualAction, VLMClient
from igris.core.state import AgentStatus, ExecutionMode


class InfiniteLoopVLM(VLMClient):
    """Simulates a VLM that keeps clicking without stopping."""
    def predict_action(self, frame, task_goal, recent_history=None):
        return VisualAction(action_type="click", normalized_x=500, normalized_y=500, reasoning="Continuous click")


@pytest.fixture(scope="module")
def safety_display():
    """Start isolated virtual display."""
    display = VirtualDisplayManager.find_free_display(start=90)
    mgr = VirtualDisplayManager(display=display, width=1920, height=1080)
    mgr.start(timeout_seconds=5.0)
    yield display
    mgr.stop()


@pytest.mark.asyncio
async def test_emergency_stop_halts_orchestrator(safety_display):
    """Verify emergency override immediately halts the active ReAct loop."""
    safety = SafetyInterlockListener()

    orchestrator = TaskOrchestrator(
        vlm_client=InfiniteLoopVLM(api_key="mock"),
        safety_listener=safety,
        max_iterations=100,
        verification_delay=0.05,
    )

    # Schedule simulated user emergency stop shortly after the task starts
    async def trigger_override_delayed():
        await asyncio.sleep(0.1)
        safety._trigger_override("Simulated user physical mouse movement")

    asyncio.create_task(trigger_override_delayed())

    summary = await orchestrator.execute_task(
        task_goal="Run indefinitely until stopped",
        mode=ExecutionMode.LIVE,
        target_display=safety_display,
    )

    assert not summary.success
    assert "Emergency override" in summary.final_message
    assert orchestrator.state.status == AgentStatus.STOPPED
    assert orchestrator.state.emergency_stop_triggered
    assert summary.total_steps < 100  # Stopped well before max iterations
