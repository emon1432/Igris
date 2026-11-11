"""Task Orchestrator: Autonomous ReAct Decision Loop (Observe -> Reason -> Act -> Verify)."""

import asyncio
import logging
import time
from typing import List, Optional
from pydantic import BaseModel, Field

from igris.action.mouse_keyboard import InputDriver
from igris.action.safety_interlock import SafetyInterlockListener
from igris.action.virtual_display import VirtualDisplayManager
from igris.brain.dispatcher import ActionDispatcher, DispatchResult
from igris.brain.vlm_client import VisualAction, VLMClient
from igris.core.state import AgentStatus, ExecutionMode, RuntimeState, TaskStepRecord
from igris.perception.accessibility import AccessibilityInspector
from igris.perception.resolver import CoordinateResolver
from igris.perception.screen import ScreenCaptureEngine

logger = logging.getLogger("igris.brain.planner")


class TaskExecutionSummary(BaseModel):
    """Final summary report of an executed autonomous task."""
    task_goal: str
    success: bool
    total_steps: int
    duration_seconds: float
    final_message: str
    history: List[TaskStepRecord] = Field(default_factory=list)


class TaskOrchestrator:
    """Manages the full ReAct loop lifecycle for autonomous computer tasks."""

    def __init__(
        self,
        vlm_client: Optional[VLMClient] = None,
        screen_engine: Optional[ScreenCaptureEngine] = None,
        accessibility_inspector: Optional[AccessibilityInspector] = None,
        dispatcher: Optional[ActionDispatcher] = None,
        virtual_display_mgr: Optional[VirtualDisplayManager] = None,
        safety_listener: Optional[SafetyInterlockListener] = None,
        state: Optional[RuntimeState] = None,
        max_iterations: int = 25,
        verification_delay: float = 0.8,
    ):
        self.state = state or RuntimeState()
        self.vlm_client = vlm_client or VLMClient()
        self.screen_engine = screen_engine or ScreenCaptureEngine()
        self.accessibility = accessibility_inspector or AccessibilityInspector()
        self.v_disp_mgr = virtual_display_mgr or VirtualDisplayManager()
        self.safety = safety_listener

        if dispatcher is None:
            input_drv = InputDriver(default_display=self.state.active_display)
            resolver = CoordinateResolver()
            self.dispatcher = ActionDispatcher(input_driver=input_drv, coordinate_resolver=resolver)
        else:
            self.dispatcher = dispatcher

        self.max_iterations = max_iterations
        self.verification_delay = verification_delay

    def _is_stuck(self, history: List[TaskStepRecord]) -> bool:
        """Detect if agent has repeated the exact same click coordinate 3 times consecutively."""
        if len(history) < 3:
            return False

        last_three = history[-3:]
        # Check if all 3 are clicks
        if not all("click" in step.action_type for step in last_three):
            return False

        coords = [step.target_coordinate for step in last_three if step.target_coordinate]
        if len(coords) < 3:
            return False

        (x1, y1), (x2, y2), (x3, y3) = coords[-3:]
        return abs(x1 - x2) <= 5 and abs(y1 - y2) <= 5 and abs(x2 - x3) <= 5 and abs(y2 - y3) <= 5

    async def execute_task(
        self,
        task_goal: str,
        mode: ExecutionMode = ExecutionMode.GHOST,
        target_display: Optional[str] = None,
    ) -> TaskExecutionSummary:
        """Run the end-to-end autonomous ReAct loop until completion, error, or override."""
        self.state.reset()
        self.state.current_task = task_goal
        self.state.current_mode = mode

        # Determine effective display
        if target_display:
            eff_display = target_display
        elif mode == ExecutionMode.GHOST:
            eff_display = self.v_disp_mgr.display
        else:
            eff_display = ":0"

        self.state.active_display = eff_display
        logger.info("Starting ReAct Loop for goal: '%s' on %s (%s)", task_goal, eff_display, mode.value)

        # Ensure virtual display is started if in Ghost mode
        is_virtual = mode == ExecutionMode.GHOST
        if is_virtual and not self.v_disp_mgr.is_active():
            self.v_disp_mgr.start()

        # Start safety listener if in Live mode
        if mode == ExecutionMode.LIVE and self.safety:
            self.safety.start()

        start_time = time.time()
        success = False
        final_message = "Task terminated."

        try:
            for iteration in range(1, self.max_iterations + 1):
                # ---------------------------------------------------------
                # 0. Safety Interlock Check
                # ---------------------------------------------------------
                if self.safety and self.safety.is_triggered:
                    self.state.status = AgentStatus.STOPPED
                    self.state.emergency_stop_triggered = True
                    final_message = "Emergency override triggered by user. Task halted immediately."
                    logger.warning(final_message)
                    break

                # ---------------------------------------------------------
                # 1. OBSERVE: Capture current frame and UI accessibility tree
                # ---------------------------------------------------------
                self.state.status = AgentStatus.OBSERVING
                frame = self.screen_engine.capture(display=eff_display)
                accessible_elements = self.accessibility.get_elements(display=eff_display)

                # ---------------------------------------------------------
                # 2. REASON: Ask VLM for next action
                # ---------------------------------------------------------
                self.state.status = AgentStatus.REASONING
                action_history_strings = [
                    f"Step {step.step_number}: {step.action_type} - {step.reasoning}"
                    for step in self.state.history
                ]

                # Inject stuck mitigation hint if needed
                if self._is_stuck(self.state.history):
                    hint = "WARNING: Previous 3 actions clicked the exact same coordinate with no state change. Try an alternative button, scroll, or press Enter."
                    action_history_strings.append(hint)
                    logger.info("Stuck condition detected; injected strategy hint to VLM.")

                action: VisualAction = self.vlm_client.predict_action(
                    frame=frame,
                    task_goal=task_goal,
                    recent_history=action_history_strings,
                )

                # Check for completion
                if action.task_completed or action.action_type.lower() == "finished":
                    self.state.status = AgentStatus.FINISHED
                    success = True
                    final_message = action.reasoning or "Task successfully achieved."
                    self.state.record_step(
                        action_type="finished",
                        reasoning=action.reasoning,
                        details="Goal completed.",
                    )
                    logger.info("Goal completed at step %d: %s", iteration, final_message)
                    break

                # ---------------------------------------------------------
                # 3. ACT: Dispatch action via mouse/keyboard or terminal
                # ---------------------------------------------------------
                self.state.status = AgentStatus.ACTING
                dispatch_res: DispatchResult = await self.dispatcher.dispatch(
                    action=action,
                    display_width=frame.width,
                    display_height=frame.height,
                    display=eff_display,
                    accessible_elements=accessible_elements,
                )

                target_coord = None
                if dispatch_res.resolved_target:
                    target_coord = (
                        dispatch_res.resolved_target.target_x,
                        dispatch_res.resolved_target.target_y,
                    )
                    # Notify safety interlock so it knows this movement was agent-driven
                    if self.safety and mode == ExecutionMode.LIVE:
                        self.safety.notify_agent_move(target_coord[0], target_coord[1])

                self.state.record_step(
                    action_type=action.action_type,
                    reasoning=action.reasoning,
                    coordinate=target_coord,
                    details=dispatch_res.details,
                )

                # ---------------------------------------------------------
                # 4. VERIFY: Pause briefly for UI updates
                # ---------------------------------------------------------
                self.state.status = AgentStatus.VERIFYING
                await asyncio.sleep(self.verification_delay)

            else:
                final_message = f"Max iteration limit ({self.max_iterations}) reached without explicit completion."
                logger.warning(final_message)

        except Exception as exc:
            self.state.status = AgentStatus.ERROR
            final_message = f"Orchestrator error encountered: {exc}"
            logger.error(final_message, exc_info=True)

        finally:
            # Stop safety listener if it was started
            if mode == ExecutionMode.LIVE and self.safety:
                self.safety.stop()

        duration = time.time() - start_time
        return TaskExecutionSummary(
            task_goal=task_goal,
            success=success,
            total_steps=self.state.step_count,
            duration_seconds=duration,
            final_message=final_message,
            history=list(self.state.history),
        )

