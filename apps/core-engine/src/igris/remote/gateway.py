"""FastAPI and WebSocket Gateway Hub for Igris Remote Mobile Companion."""

import asyncio
import base64
import io
import logging
import os
import time
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from igris.brain.planner import TaskExecutionSummary, TaskOrchestrator
from igris.core.state import AgentStatus, ExecutionMode
from igris.perception.screen import ScreenCaptureEngine
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

logger = logging.getLogger("igris.remote.gateway")


class ConnectionManager:
    """Manages active companion WebSocket connections and broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.background_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()

    def track_task(self, task: asyncio.Task) -> asyncio.Task:
        """Keep a strong reference to background task to prevent premature garbage collection."""
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return task

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info("Companion client connected (Total active: %d)", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info("Companion client disconnected (Remaining: %d)", len(self.active_connections))

    async def broadcast(self, envelope: CompanionEnvelope) -> None:
        """Broadcast message envelope to all connected companion clients."""
        payload_json = envelope.model_dump_json()
        async with self._lock:
            dead_sockets = set()
            for ws in self.active_connections:
                try:
                    await ws.send_text(payload_json)
                except Exception as e:
                    logger.debug("Failed to send WebSocket broadcast: %s", e)
                    dead_sockets.add(ws)
            self.active_connections.difference_update(dead_sockets)

    async def send_personal(self, websocket: WebSocket, envelope: CompanionEnvelope) -> None:
        """Send message directly to a single client socket."""
        try:
            await websocket.send_text(envelope.model_dump_json())
        except Exception as e:
            logger.debug("Failed to send direct WebSocket message: %s", e)


def create_gateway_app(
    orchestrator: Optional[TaskOrchestrator] = None,
    screen_engine: Optional[ScreenCaptureEngine] = None,
    auth_token: str = "igris-secure-token",
    static_web_dir: Optional[str] = None,
) -> FastAPI:
    """Create and configure the FastAPI companion gateway application."""
    app = FastAPI(title="Igris Remote Companion Gateway", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()
    orch = orchestrator or TaskOrchestrator()
    screen = screen_engine or ScreenCaptureEngine()
    server_start_time = time.time()

    # -------------------------------------------------------------
    # REST Endpoints
    # -------------------------------------------------------------

    @app.get("/api/system/health", response_model=SystemStatusMessage)
    async def get_health():
        return SystemStatusMessage(
            agent_status=orch.state.status.value,
            active_display=orch.state.active_display,
            active_task=orch.state.current_goal,
            connected_clients=len(manager.active_connections),
            uptime_seconds=round(time.time() - server_start_time, 2),
        )

    @app.get("/api/screen/preview")
    async def get_screen_preview():
        """Capture and return current screen as a downscaled JPEG image."""
        try:
            frame = screen.capture(display=orch.state.active_display)
            thumb_frame = frame.downscale(max_dimension=960)
            jpeg_bytes = thumb_frame.to_bytes(format="JPEG", quality=70)
            return Response(content=jpeg_bytes, media_type="image/jpeg")
        except Exception as e:
            logger.error("Screen preview capture failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/emergency/stop")
    async def emergency_stop():
        """Trigger emergency stop to immediately halt active orchestrator tasks."""
        logger.warning("Emergency stop requested via REST API.")
        orch.state.status = AgentStatus.STOPPED
        orch.state.emergency_stop_triggered = True
        if orch.safety:
            orch.safety._override_triggered = True

        stop_msg = CompanionEnvelope(
            type=MessageType.EMERGENCY_STOP,
            payload={"reason": "Emergency stop invoked via REST API"},
        )
        await manager.broadcast(stop_msg)
        return {"status": "emergency_stop_triggered", "success": True}

    @app.post("/api/task/execute")
    async def execute_task_endpoint(cmd: TaskCommand):
        """Execute task asynchronously in background ReAct loop."""
        mode = ExecutionMode.LIVE if cmd.mode.lower() == "live" else ExecutionMode.GHOST

        # Launch background task execution
        async def run_bg():
            summary = await orch.execute_task(
                task_goal=cmd.task_goal,
                mode=mode,
            )
            # Broadcast completion
            comp_msg = CompanionEnvelope(
                type=MessageType.TASK_COMPLETED,
                payload=TaskCompletedMessage(
                    task_goal=cmd.task_goal,
                    success=summary.success,
                    total_steps=summary.total_steps,
                    duration_seconds=summary.duration_seconds,
                    final_message=summary.final_message,
                ).model_dump(),
            )
            await manager.broadcast(comp_msg)

        manager.track_task(asyncio.create_task(run_bg()))
        return {"status": "task_dispatched", "goal": cmd.task_goal, "mode": cmd.mode}

    # -------------------------------------------------------------
    # WebSocket Companion Hub
    # -------------------------------------------------------------

    @app.websocket("/ws/companion")
    async def websocket_companion_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        authenticated = False

        try:
            while True:
                data_text = await websocket.receive_text()
                try:
                    import json
                    raw = json.loads(data_text)
                    msg_type = raw.get("type")
                    payload = raw.get("payload", {})

                    if msg_type == MessageType.AUTH_REQUEST.value:
                        req_token = payload.get("token", "")
                        if req_token == auth_token or not auth_token:
                            authenticated = True
                            resp = CompanionEnvelope(
                                type=MessageType.AUTH_RESPONSE,
                                payload=AuthResponse(
                                    authenticated=True,
                                    message="Authenticated successfully",
                                    session_id="igris-live-session",
                                ).model_dump(),
                            )
                            await manager.send_personal(websocket, resp)
                            logger.info("Client authenticated successfully.")
                        else:
                            resp = CompanionEnvelope(
                                type=MessageType.AUTH_RESPONSE,
                                payload=AuthResponse(
                                    authenticated=False,
                                    message="Invalid authorization token",
                                ).model_dump(),
                            )
                            await manager.send_personal(websocket, resp)

                    elif not authenticated:
                        err = CompanionEnvelope(
                            type=MessageType.ERROR,
                            payload={"error": "Unauthorized. Please authenticate first."},
                        )
                        await manager.send_personal(websocket, err)

                    elif msg_type == MessageType.TASK_COMMAND.value:
                        cmd = TaskCommand(**payload)
                        mode = ExecutionMode.LIVE if cmd.mode.lower() == "live" else ExecutionMode.GHOST

                        # Notify client task started
                        start_update = CompanionEnvelope(
                            type=MessageType.TASK_UPDATE,
                            payload=TaskUpdateMessage(
                                step_number=0,
                                action_type="starting",
                                thought=f"Starting task: {cmd.task_goal}",
                                status="started",
                            ).model_dump(),
                        )
                        await manager.broadcast(start_update)

                        # Run task
                        async def run_ws_task():
                            summary = await orch.execute_task(
                                task_goal=cmd.task_goal,
                                mode=mode,
                            )
                            complete_env = CompanionEnvelope(
                                type=MessageType.TASK_COMPLETED,
                                payload=TaskCompletedMessage(
                                    task_goal=cmd.task_goal,
                                    success=summary.success,
                                    total_steps=summary.total_steps,
                                    duration_seconds=summary.duration_seconds,
                                    final_message=summary.final_message,
                                ).model_dump(),
                            )
                            await manager.broadcast(complete_env)

                        manager.track_task(asyncio.create_task(run_ws_task()))

                    elif msg_type == MessageType.EMERGENCY_STOP.value:
                        logger.warning("Emergency stop received via WebSocket.")
                        orch.state.status = AgentStatus.STOPPED
                        orch.state.emergency_stop_triggered = True
                        if orch.safety:
                            orch.safety._override_triggered = True

                        stop_broadcast = CompanionEnvelope(
                            type=MessageType.EMERGENCY_STOP,
                            payload={"reason": "Emergency stop triggered by client"},
                        )
                        await manager.broadcast(stop_broadcast)

                except Exception as parse_err:
                    logger.error("Error processing WebSocket message: %s", parse_err)
                    err_env = CompanionEnvelope(
                        type=MessageType.ERROR,
                        payload={"error": str(parse_err)},
                    )
                    await manager.send_personal(websocket, err_env)

        except WebSocketDisconnect:
            await manager.disconnect(websocket)

    # -------------------------------------------------------------
    # Optional Static Web PWA Mount
    # -------------------------------------------------------------
    web_dir = static_web_dir or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../companion-web")
    )
    if os.path.exists(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="companion-web")
        logger.info("Mounted Companion Web App from: %s", web_dir)

    return app
