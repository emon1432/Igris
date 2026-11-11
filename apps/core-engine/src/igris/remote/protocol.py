"""Protocol definitions and RPC message schemas for Igris Remote Companion Gateway."""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    AUTH_REQUEST = "auth_request"
    AUTH_RESPONSE = "auth_response"
    TASK_COMMAND = "task_command"
    TASK_UPDATE = "task_update"
    TASK_COMPLETED = "task_completed"
    SCREEN_FRAME = "screen_frame"
    EMERGENCY_STOP = "emergency_stop"
    VOICE_AUDIO_CHUNK = "voice_audio_chunk"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"


class AuthRequest(BaseModel):
    """Client authentication payload."""
    token: str = Field(..., description="Pre-shared authentication token or PIN")
    client_id: str = Field(default="companion-client", description="Unique identifier for client device")
    device_type: str = Field(default="mobile", description="Device platform (mobile, web, tablet)")


class AuthResponse(BaseModel):
    """Server authentication response."""
    authenticated: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Status explanation")
    session_id: Optional[str] = Field(default=None, description="Active session ID if authenticated")


class TaskCommand(BaseModel):
    """Remote task execution instruction sent by client."""
    task_goal: str = Field(..., description="High-level autonomous objective for Igris")
    mode: str = Field(default="ghost", description="Execution mode: 'ghost' or 'live'")
    max_iterations: int = Field(default=15, description="Maximum ReAct steps allowed")


class TaskUpdateMessage(BaseModel):
    """Real-time progress update for an ongoing task."""
    step_number: int
    action_type: str
    thought: str
    target_x: Optional[int] = None
    target_y: Optional[int] = None
    status: str = Field(default="in_progress")
    timestamp: float = Field(default_factory=time.time)


class TaskCompletedMessage(BaseModel):
    """Final result notification when task concludes."""
    task_goal: str
    success: bool
    total_steps: int
    duration_seconds: float
    final_message: str
    timestamp: float = Field(default_factory=time.time)


class ScreenFrameMessage(BaseModel):
    """Live screen capture frame encoded as base64 JPEG for canvas rendering."""
    frame_b64: str = Field(..., description="Base64 encoded JPEG preview")
    width: int
    height: int
    timestamp: float = Field(default_factory=time.time)


class EmergencyStopMessage(BaseModel):
    """Immediate abort trigger initiated from mobile/remote client."""
    source: str = Field(default="remote_companion")
    reason: str = Field(default="Emergency stop triggered by user")
    timestamp: float = Field(default_factory=time.time)


class SystemStatusMessage(BaseModel):
    """Host machine and Igris agent status heartbeat."""
    agent_status: str
    active_display: str
    active_task: Optional[str] = None
    connected_clients: int = 0
    uptime_seconds: float = 0.0


class CompanionEnvelope(BaseModel):
    """Standard envelope wrapping all WebSocket messages."""
    type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

