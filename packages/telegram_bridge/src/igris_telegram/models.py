"""Data Models for Telegram Push Notifications & Inline Button Approvals."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class TelegramNotification(BaseModel):
    """Outgoing push alert message."""
    chat_id: str
    text: str
    priority: str = "NORMAL"  # "NORMAL" | "HIGH" | "CRITICAL"
    timestamp: float


class TelegramApprovalPrompt(BaseModel):
    """Interactive approval message rendered with Telegram inline keyboard buttons."""
    request_id: str
    chat_id: str
    action_type: str
    risk_tier: str
    formatted_message: str
    inline_buttons: List[List[Dict[str, str]]] = Field(default_factory=list)

