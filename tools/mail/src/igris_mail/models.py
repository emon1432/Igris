"""Data Models for Mail Ingestion, Triage and Drafts."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    """Raw incoming email message."""
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    received_at: float = 0.0
    is_spoofed: bool = False
    claimed_amount_usd: Optional[float] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class EmailSummary(BaseModel):
    """Triage summarization artifact."""
    id: str
    sender: str
    sender_verified: bool
    client_id: Optional[str] = None
    summary: str
    security_warning: Optional[str] = None
    has_financial_claim: bool = False
    claimed_amount_usd: Optional[float] = None


class EmailDraft(BaseModel):
    """Synthesized reply draft (Data only, not sent)."""
    draft_id: str
    in_reply_to_id: str
    recipient: str
    subject: str
    body: str
    security_warning: Optional[str] = None
    financial_status: str = "NONE"  # "VERIFIED" | "UNVERIFIED_CLAIM" | "NONE"
    is_sent: bool = False
    payload_hash: Optional[str] = None

