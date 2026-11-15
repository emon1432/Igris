"""Mail Operations Tool (Triage, Verified Drafts & Gated T3 Dispatch).

Guarantees:
1. Triage Mode: Read-only inbox reading, sanitization, and summary generation.
2. Sender Verification (I-02): Identifies and alerts on unverified or spoofed senders.
3. Financial Verification (F-01): Mandates system-of-record checks before allowing payment statements.
   Unverified claims are stamped with [UNVERIFIED CLAIM].
4. Outbound Sending is Gated T3: Strictly requires an on-screen button ApprovalToken matching the draft hash.
"""

import hashlib
import time
from typing import List, Dict, Optional, Any
from igris_protocol.models import RiskTier, ApprovalToken
from igris_registry.registry import ProjectRegistry
from igris_mail.models import EmailMessage, EmailSummary, EmailDraft
from igris_mail.parser import UntrustedEmailParser


class MailToolError(RuntimeError):
    """Raised when a mail operation fails security or execution constraints."""
    pass


class MailTool:
    """Manages email triage, verified drafting, and gated outbound delivery."""

    def __init__(self, inbox_storage: Optional[List[EmailMessage]] = None):
        self._inbox: List[EmailMessage] = inbox_storage or []
        self._drafts: Dict[str, EmailDraft] = {}

    def add_message(self, message: EmailMessage):
        """Adds a message to the inbox."""
        self._inbox.append(message)

    def fetch_inbox(self, folder: str = "INBOX", limit: int = 10) -> List[EmailMessage]:
        """Fetches inbox messages for read-only triage (T0)."""
        return list(self._inbox[:limit])

    def verify_sender(self, sender_email: str, registry: Optional[ProjectRegistry]) -> Dict[str, Any]:
        """Checks sender email address against registered client contacts (I-02)."""
        if not registry:
            return {"verified": False, "client_id": None, "warning": "REGISTRY_UNAVAILABLE"}

        for client_id in registry.list_clients():
            client = registry.get_client(client_id)
            if client and sender_email.lower() in [s.lower() for s in client.verified_senders]:
                return {"verified": True, "client_id": client.client_id, "warning": None}

        return {
            "verified": False,
            "client_id": None,
            "warning": f"UNVERIFIED_SENDER: Address '{sender_email}' is not registered under any client.",
        }

    def triage_summary(
        self,
        message: EmailMessage,
        registry: Optional[ProjectRegistry] = None,
    ) -> EmailSummary:
        """Produces a safe, sanitized triage summary of an incoming email."""
        parsed = UntrustedEmailParser.sanitize_body(message.body)
        sender_check = self.verify_sender(message.sender, registry)

        sec_warning = None
        if not sender_check["verified"]:
            sec_warning = sender_check["warning"]
        if parsed["has_injection_signals"]:
            injection_note = "INJECTION_ATTEMPT_DETECTED: Suspicious instruction patterns neutralized."
            sec_warning = f"{sec_warning} | {injection_note}" if sec_warning else injection_note

        has_fin = message.claimed_amount_usd is not None and message.claimed_amount_usd > 0
        summary_text = f"Subject: {message.subject}. Sender: {message.sender}."

        return EmailSummary(
            id=message.id,
            sender=message.sender,
            sender_verified=sender_check["verified"],
            client_id=sender_check["client_id"],
            summary=summary_text,
            security_warning=sec_warning,
            has_financial_claim=has_fin,
            claimed_amount_usd=message.claimed_amount_usd,
        )

    def create_reply_draft(
        self,
        message: EmailMessage,
        body_content: str,
        registry: Optional[ProjectRegistry] = None,
        system_of_record: Optional[Dict[str, float]] = None,
    ) -> EmailDraft:
        """Synthesizes an inert reply draft with sender and financial claim validation (F-01, I-02)."""
        sender_check = self.verify_sender(message.sender, registry)
        sec_warning = sender_check.get("warning") if not sender_check["verified"] else None

        financial_status = "NONE"
        final_body = body_content

        # Financial verification (F-01)
        if message.claimed_amount_usd is not None and message.claimed_amount_usd > 0:
            claimed = message.claimed_amount_usd
            client_id = sender_check.get("client_id")
            recorded_balance = (system_of_record or {}).get(client_id, 0.0) if client_id else 0.0

            if recorded_balance < claimed:
                financial_status = "UNVERIFIED_CLAIM"
                watermark = (
                    f"[UNVERIFIED CLAIM: Payment of ${claimed:.2f} is NOT confirmed in accounting records. "
                    "Do not acknowledge receipt as settled until reconciled.]\n\n"
                )
                final_body = watermark + final_body
            else:
                financial_status = "VERIFIED"

        if sec_warning:
            final_body = f"[{sec_warning}]\n\n" + final_body

        draft_id = f"draft_{int(time.time() * 1000)}"
        payload_hash = hashlib.sha256(final_body.encode("utf-8")).hexdigest()

        draft = EmailDraft(
            draft_id=draft_id,
            in_reply_to_id=message.id,
            recipient=message.sender,
            subject=f"Re: {message.subject}",
            body=final_body,
            security_warning=sec_warning,
            financial_status=financial_status,
            payload_hash=payload_hash,
        )

        self._drafts[draft_id] = draft
        return draft

    def send_email_outbound(
        self,
        draft_id: str,
        approval_token: Optional[ApprovalToken] = None,
    ) -> Dict[str, Any]:
        """Dispatches an outbound email (T3). Strictly gated by screen button approval token."""
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError(f"Draft '{draft_id}' not found.")

        # 1. Approval token requirement
        if approval_token is None:
            raise PermissionError("GATED_ACTION: Outbound email dispatch requires explicit T3 screen button approval.")

        # 2. Risk tier check
        if approval_token.risk_tier != RiskTier.T3:
            raise PermissionError(f"GATED_ACTION: Outbound email requires risk tier T3 (got {approval_token.risk_tier}).")

        # 3. Channel restriction (Voice cannot approve)
        if approval_token.granted_by != "SCREEN_BUTTON":
            raise PermissionError("GATED_ACTION: Outbound email cannot be authorized via voice.")

        # 4. Hash verification
        if approval_token.payload_hash != draft.payload_hash:
            raise PermissionError("GATED_ACTION: Payload hash mismatch. The draft was modified after approval was requested.")

        draft.is_sent = True
        return {
            "status": "EMAIL_SENT",
            "draft_id": draft.draft_id,
            "recipient": draft.recipient,
            "subject": draft.subject,
            "approval_token_id": approval_token.token_id,
            "timestamp": time.time(),
        }

