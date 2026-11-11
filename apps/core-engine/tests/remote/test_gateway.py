"""Tests for FastAPI and WebSocket companion gateway."""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from igris.brain.planner import TaskExecutionSummary, TaskOrchestrator
from igris.perception.screen import ScreenCaptureEngine, ScreenFrame
from igris.remote.gateway import create_gateway_app
from igris.remote.protocol import MessageType


@pytest.fixture
def mock_orchestrator():
    orch = MagicMock(spec=TaskOrchestrator)
    orch.state = MagicMock()
    orch.state.status.value = "idle"
    orch.state.active_display = ":99"
    orch.state.current_goal = None
    orch.state.emergency_stop_triggered = False
    orch.safety = MagicMock()
    orch.execute_task = AsyncMock(
        return_value=TaskExecutionSummary(
            task_goal="test goal",
            success=True,
            total_steps=1,
            duration_seconds=0.5,
            final_message="Test task complete",
        )
    )
    return orch


@pytest.fixture
def mock_screen_engine():
    engine = MagicMock(spec=ScreenCaptureEngine)
    # Return synthetic PIL Image in ScreenFrame
    img = Image.new("RGB", (100, 100), color="blue")
    frame = ScreenFrame(raw_image=img, width=100, height=100, display=":99", duration_ms=10.0)
    engine.capture.return_value = frame
    return engine


def test_rest_health_check(mock_orchestrator, mock_screen_engine):
    """Verify system health endpoint returns proper status."""
    app = create_gateway_app(
        orchestrator=mock_orchestrator,
        screen_engine=mock_screen_engine,
    )
    client = TestClient(app)

    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_status"] == "idle"
    assert data["active_display"] == ":99"
    assert "uptime_seconds" in data


def test_rest_screen_preview(mock_orchestrator, mock_screen_engine):
    """Verify screen preview returns JPEG image bytes."""
    app = create_gateway_app(
        orchestrator=mock_orchestrator,
        screen_engine=mock_screen_engine,
    )
    client = TestClient(app)

    response = client.get("/api/screen/preview")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_rest_emergency_stop(mock_orchestrator, mock_screen_engine):
    """Verify emergency stop endpoint halts orchestrator."""
    app = create_gateway_app(
        orchestrator=mock_orchestrator,
        screen_engine=mock_screen_engine,
    )
    client = TestClient(app)

    response = client.post("/api/emergency/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "emergency_stop_triggered"
    assert mock_orchestrator.state.emergency_stop_triggered is True


def test_websocket_companion_auth_and_messaging(mock_orchestrator, mock_screen_engine):
    """Verify WebSocket handshake, authentication, and message exchange."""
    app = create_gateway_app(
        orchestrator=mock_orchestrator,
        screen_engine=mock_screen_engine,
        auth_token="secret-123",
    )
    client = TestClient(app)

    with client.websocket_connect("/ws/companion") as websocket:
        # 1. Try sending command before authenticating -> Expect error
        websocket.send_text(json.dumps({
            "type": MessageType.TASK_COMMAND.value,
            "payload": {"task_goal": "Do something"}
        }))
        err_msg = json.loads(websocket.receive_text())
        assert err_msg["type"] == MessageType.ERROR.value

        # 2. Send invalid token
        websocket.send_text(json.dumps({
            "type": MessageType.AUTH_REQUEST.value,
            "payload": {"token": "wrong-token"}
        }))
        auth_fail = json.loads(websocket.receive_text())
        assert auth_fail["type"] == MessageType.AUTH_RESPONSE.value
        assert auth_fail["payload"]["authenticated"] is False

        # 3. Send valid token
        websocket.send_text(json.dumps({
            "type": MessageType.AUTH_REQUEST.value,
            "payload": {"token": "secret-123"}
        }))
        auth_ok = json.loads(websocket.receive_text())
        assert auth_ok["type"] == MessageType.AUTH_RESPONSE.value
        assert auth_ok["payload"]["authenticated"] is True

        # 4. Send emergency stop
        websocket.send_text(json.dumps({
            "type": MessageType.EMERGENCY_STOP.value,
            "payload": {"reason": "User abort"}
        }))
        stop_resp = json.loads(websocket.receive_text())
        assert stop_resp["type"] == MessageType.EMERGENCY_STOP.value
