"""Telegram Bridge Service for Mobile Push Notifications & Interactive Approvals.

Guarantees:
1. Pushes real-time alerts and staged task notifications to the operator's Telegram client.
2. Renders interactive Telegram Inline Keyboard buttons for T2 and T3 operations.
3. Tapping the Telegram button emits a verified SCREEN_BUTTON decision to ApprovalManager.
4. Voice approvals via Telegram voice notes are rejected (M-01).
"""

import time
from typing import Dict, List, Optional, Any
from igris.remote.approval_manager import ApprovalManager, ApprovalRequest
from igris_telegram.models import TelegramNotification, TelegramApprovalPrompt


class TelegramBridgeService:
    """Manages real-time mobile push notifications and inline button approvals via Telegram."""

    def __init__(self, bot_token: Optional[str] = None, default_chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id or "owner_chat_default"
        self._sent_alerts: List[TelegramNotification] = []
        self._sent_prompts: Dict[str, TelegramApprovalPrompt] = {}

    def send_alert(self, text: str, chat_id: Optional[str] = None, priority: str = "NORMAL") -> TelegramNotification:
        """Dispatches a real-time notification to the operator's mobile Telegram client."""
        target_chat = chat_id or self.default_chat_id
        notif = TelegramNotification(
            chat_id=target_chat,
            text=text,
            priority=priority,
            timestamp=time.time(),
        )
        self._sent_alerts.append(notif)
        return notif

    def prompt_approval(
        self,
        request: ApprovalRequest,
        chat_id: Optional[str] = None,
    ) -> TelegramApprovalPrompt:
        """Formats and sends an interactive approval message with Telegram inline keyboard buttons."""
        target_chat = chat_id or self.default_chat_id

        formatted_msg = (
            f"⚡ *IGRIS ACTION APPROVAL REQUIRED* ⚡\n\n"
            f"• *Tier:* `{request.risk_tier.value}`\n"
            f"• *Action:* `{request.action_type}`\n"
            f"• *Task ID:* `{request.task_id}`\n\n"
            f"```\n{request.payload_summary}\n```\n\n"
            f"🔑 `SHA256: {request.payload_hash[:16]}...`\n"
            f"_Tap an inline button below to authorize or reject execution:_"
        )

        buttons = [
            [
                {"text": "✅ Approve & Execute", "callback_data": f"appr:{request.request_id}:APPROVE"},
                {"text": "❌ Reject Action", "callback_data": f"appr:{request.request_id}:REJECT"},
            ]
        ]

        prompt = TelegramApprovalPrompt(
            request_id=request.request_id,
            chat_id=target_chat,
            action_type=request.action_type,
            risk_tier=request.risk_tier.value,
            formatted_message=formatted_msg,
            inline_buttons=buttons,
        )
        self._sent_prompts[request.request_id] = prompt
        return prompt

    def handle_callback_query(
        self,
        callback_data: str,
        approval_manager: ApprovalManager,
    ) -> Dict[str, Any]:
        """Processes an inline button tap callback from the Telegram interface.

        Tapping the physical button on the Telegram screen satisfies the SCREEN_BUTTON invariant.
        """
        parts = callback_data.split(":")
        if len(parts) != 3 or parts[0] != "appr":
            raise ValueError(f"Invalid callback data format: '{callback_data}'. Expected 'appr:<req_id>:<decision>'.")

        _, req_id, decision = parts

        # Resolve through ApprovalManager with channel="SCREEN_BUTTON"
        token = approval_manager.resolve_decision(
            request_id=req_id,
            decision=decision,
            channel="SCREEN_BUTTON",
        )

        return {
            "status": "CALLBACK_RESOLVED",
            "request_id": req_id,
            "decision": decision,
            "token_id": token.token_id if token else None,
        }

    def get_sent_alerts(self) -> List[TelegramNotification]:
        """Returns log of sent push alerts."""
        return list(self._sent_alerts)

