"""Runtime State Manager for Igris."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    LIVE = "live"
    GHOST = "ghost"


class AgentStatus(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    ACTING = "acting"
    VERIFYING = "verifying"
    WAITING_CONFIRMATION = "waiting_confirmation"
    ERROR = "error"


class RuntimeState(BaseModel):
    current_mode: ExecutionMode = ExecutionMode.GHOST
    status: AgentStatus = AgentStatus.IDLE
    active_display: str = ":99"
    current_task: Optional[str] = None
    step_count: int = 0
    emergency_stop_triggered: bool = False
    last_action: Optional[str] = None
