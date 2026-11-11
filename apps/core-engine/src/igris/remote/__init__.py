"""Remote companion gateway package for mobile communication, WebSockets, and PWA interface."""

from igris.remote.protocol import (
    AuthRequest,
    AuthResponse,
    CompanionEnvelope,
    EmergencyStopMessage,
    MessageType,
    ScreenFrameMessage,
    SystemStatusMessage,
    TaskCommand,
    TaskCompletedMessage,
    TaskUpdateMessage,
)
from igris.remote.gateway import ConnectionManager, create_gateway_app

__all__ = [
    "AuthRequest",
    "AuthResponse",
    "CompanionEnvelope",
    "EmergencyStopMessage",
    "MessageType",
    "ScreenFrameMessage",
    "SystemStatusMessage",
    "TaskCommand",
    "TaskCompletedMessage",
    "TaskUpdateMessage",
    "ConnectionManager",
    "create_gateway_app",
]
