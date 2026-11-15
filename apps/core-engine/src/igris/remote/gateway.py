"""FastAPI and WebSocket Gateway Hub for Igris Remote Mobile Companion."""

import asyncio
import base64
import io
import json
import logging
import os
import time
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from igris.brain.planner import TaskExecutionSummary, TaskOrchestrator
from igris.brain.conversational_mind import ConversationalMind, UserIntent
from igris.core.state import AgentStatus, ExecutionMode
from igris.perception.screen import ScreenCaptureEngine
from igris.remote.approval_manager import (
    ApprovalManager,
    global_approval_manager,
    VoiceApprovalDisallowedError,
)
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


class DecisionPayload(BaseModel):
    decision: str  # "APPROVE" | "REJECT"
    channel: str = "SCREEN_BUTTON"


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
    approval_manager: Optional[ApprovalManager] = None,
    conversational_mind: Optional[ConversationalMind] = None,
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
    approvals = approval_manager or global_approval_manager
    mind = conversational_mind or ConversationalMind()
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
    async def get_screen_preview(display: Optional[str] = None):
        """Capture and return current screen as a downscaled JPEG image."""
        try:
            target_disp = display or orch.state.active_display
            frame = screen.capture(display=target_disp)
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

    @app.get("/api/approvals/pending")
    async def get_pending_approvals():
        """Returns active staged approvals awaiting screen button confirmation."""
        active = approvals.get_pending_requests()
        return [req.model_dump() for req in active]

    @app.post("/api/approvals/{request_id}/decision")
    async def submit_approval_decision(request_id: str, payload: DecisionPayload):
        """Submit approval decision from on-screen UI button (M-01 enforcement)."""
        try:
            token = approvals.resolve_decision(
                request_id=request_id,
                decision=payload.decision,
                channel=payload.channel,
            )
            resp = {
                "success": True,
                "request_id": request_id,
                "decision": payload.decision,
                "token_id": token.token_id if token else None,
            }
            # Broadcast resolution
            broadcast_env = CompanionEnvelope(
                type=MessageType.TASK_UPDATE,
                payload={
                    "step_number": 0,
                    "action_type": "approval_resolved",
                    "thought": f"Approval {request_id} resolved: {payload.decision}",
                    "status": "approved" if token else "rejected",
                },
            )
            await manager.broadcast(broadcast_env)
            return resp
        except VoiceApprovalDisallowedError as vad_err:
            raise HTTPException(status_code=400, detail=str(vad_err))
        except KeyError as ke:
            raise HTTPException(status_code=404, detail=str(ke))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/task/execute")
    async def execute_task_endpoint(cmd: TaskCommand):
        """Execute task asynchronously with conversational intent routing."""
        routing = mind.route_request(cmd.task_goal)

        # Conversational Fast Path (Greetings / Status / Chit-chat)
        if not routing["execute_os_actions"]:
            comp_msg = CompanionEnvelope(
                type=MessageType.TASK_COMPLETED,
                payload=TaskCompletedMessage(
                    task_goal=cmd.task_goal,
                    success=True,
                    total_steps=1,
                    duration_seconds=0.1,
                    final_message=routing["response"],
                ).model_dump(),
            )
            await manager.broadcast(comp_msg)
            return {"status": "conversational_completed", "response": routing["response"]}

        # Operational Computer Operating Task Path
        mode = ExecutionMode.LIVE if cmd.mode.lower() == "live" else ExecutionMode.GHOST

        async def run_bg():
            async def on_step(step_rec, status):
                step_env = CompanionEnvelope(
                    type=MessageType.TASK_UPDATE,
                    payload=TaskUpdateMessage(
                        step_number=step_rec.step_number,
                        action_type=step_rec.action_type,
                        thought=step_rec.reasoning,
                        coordinate=step_rec.target_coordinate,
                        status=status.value,
                    ).model_dump(),
                )
                await manager.broadcast(step_env)

            summary = await orch.execute_task(
                task_goal=cmd.task_goal,
                mode=mode,
                step_callback=on_step,
            )
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
                        routing = mind.route_request(cmd.task_goal)

                        # Conversational Fast Path (No browser/desktop actions!)
                        if not routing["execute_os_actions"]:
                            comp_msg = CompanionEnvelope(
                                type=MessageType.TASK_COMPLETED,
                                payload=TaskCompletedMessage(
                                    task_goal=cmd.task_goal,
                                    success=True,
                                    total_steps=1,
                                    duration_seconds=0.1,
                                    final_message=routing["response"],
                                ).model_dump(),
                            )
                            await manager.broadcast(comp_msg)
                            continue

                        # Operational Computer Task Path
                        mode = ExecutionMode.LIVE if cmd.mode.lower() == "live" else ExecutionMode.GHOST

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

                        async def run_ws_task():
                            async def on_ws_step(step_rec, status):
                                step_env = CompanionEnvelope(
                                    type=MessageType.TASK_UPDATE,
                                    payload=TaskUpdateMessage(
                                        step_number=step_rec.step_number,
                                        action_type=step_rec.action_type,
                                        thought=step_rec.reasoning,
                                        coordinate=step_rec.target_coordinate,
                                        status=status.value,
                                    ).model_dump(),
                                )
                                await manager.broadcast(step_env)

                            summary = await orch.execute_task(
                                task_goal=cmd.task_goal,
                                mode=mode,
                                step_callback=on_ws_step,
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

                    elif msg_type == "APPROVAL_DECISION":
                        req_id = payload.get("request_id")
                        decision = payload.get("decision", "APPROVE")
                        channel = payload.get("channel", "SCREEN_BUTTON")
                        try:
                            token = approvals.resolve_decision(req_id, decision, channel)
                            ack = CompanionEnvelope(
                                type=MessageType.TASK_UPDATE,
                                payload={
                                    "step_number": 0,
                                    "action_type": "approval_resolved",
                                    "thought": f"Approval {req_id} decision: {decision}",
                                    "status": "approved" if token else "rejected",
                                },
                            )
                            await manager.broadcast(ack)
                        except Exception as e:
                            err_env = CompanionEnvelope(
                                type=MessageType.ERROR,
                                payload={"error": str(e)},
                            )
                            await manager.send_personal(websocket, err_env)

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


# Default ASGI application instance for uvicorn runner
app = create_gateway_app()
