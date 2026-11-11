"""Tests for Remote Companion message protocol schemas."""

import json
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


def test_auth_schemas():
    """Verify auth request and response serialization."""
    req = AuthRequest(token="test-token", client_id="unit-test-mobile")
    assert req.token == "test-token"
    assert req.device_type == "mobile"

    resp = AuthResponse(authenticated=True, message="Success", session_id="sess-123")
    assert resp.authenticated
    assert resp.session_id == "sess-123"


def test_task_command_and_updates():
    """Verify task command and update message models."""
    cmd = TaskCommand(task_goal="Search for flight tickets", mode="ghost")
    assert cmd.task_goal == "Search for flight tickets"
    assert cmd.mode == "ghost"
    assert cmd.max_iterations == 15

    update = TaskUpdateMessage(
        step_number=2,
        action_type="click",
        thought="Clicking flight search input",
        target_x=450,
        target_y=320,
    )
    assert update.step_number == 2
    assert update.target_x == 450

    completed = TaskCompletedMessage(
        task_goal="Search for flight tickets",
        success=True,
        total_steps=5,
        duration_seconds=4.2,
        final_message="Flights found and listed.",
    )
    assert completed.success
    assert completed.total_steps == 5


def test_companion_envelope_json_roundtrip():
    """Verify envelope serialization and deserialization."""
    stop_msg = EmergencyStopMessage(source="mobile_widget", reason="User tapped abort")
    env = CompanionEnvelope(
        type=MessageType.EMERGENCY_STOP,
        payload=stop_msg.model_dump(),
    )

    json_str = env.model_dump_json()
    assert "emergency_stop" in json_str
    assert "User tapped abort" in json_str

    parsed = CompanionEnvelope(**json.loads(json_str))
    assert parsed.type == MessageType.EMERGENCY_STOP
    assert parsed.payload["source"] == "mobile_widget"

