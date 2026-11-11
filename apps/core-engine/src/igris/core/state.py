"""Runtime State Manager for Igris."""

import time
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    LIVE = "live"
    GHOST = "ghost"


class AgentStatus(str, Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    REASONING = "reasoning"
    ACTING = "acting"
    VERIFYING = "verifying"
    WAITING_CONFIRMATION = "waiting_confirmation"
    FINISHED = "finished"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStepRecord(BaseModel):
    """Historical snapshot of a single executed step in the ReAct loop."""
    step_number: int
    action_type: str
    reasoning: str
    target_coordinate: Optional[Tuple[int, int]] = None
    details: str = ""
    timestamp: float = Field(default_factory=time.time)


class RuntimeState(BaseModel):
    """Global live state of the autonomous operator daemon."""
    current_mode: ExecutionMode = ExecutionMode.GHOST
    status: AgentStatus = AgentStatus.IDLE
    active_display: str = ":99"
    current_task: Optional[str] = None
    step_count: int = 0
    emergency_stop_triggered: bool = False
    last_action: Optional[str] = None
    history: List[TaskStepRecord] = Field(default_factory=list)

    def record_step(
        self,
        action_type: str,
        reasoning: str,
        coordinate: Optional[Tuple[int, int]] = None,
        details: str = "",
    ) -> TaskStepRecord:
        """Add an executed step record to history and increment step counter."""
        self.step_count += 1
        record = TaskStepRecord(
            step_number=self.step_count,
            action_type=action_type,
            reasoning=reasoning,
            target_coordinate=coordinate,
            details=details,
        )
        self.history.append(record)
        self.last_action = f"{action_type}: {details}"
        return record

    def reset(self) -> None:
        """Reset task-specific runtime state."""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.step_count = 0
        self.emergency_stop_triggered = False
        self.last_action = None
        self.history.clear()
