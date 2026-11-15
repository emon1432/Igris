"""Approval Manager Subsystem & Voice Approval Boundary (M-01).

Guarantees:
1. Manages pending approval requests staged by Orchestrator or Tools.
2. M-01 Invariant: Enforces that T2 and T3 authorizations must originate from a physical
   SCREEN_BUTTON click. Vocal confirmations (VOICE) are rejected deterministically.
3. Issues cryptographically hashed ApprovalTokens upon valid screen button confirmation.
"""

import hashlib
import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from igris_protocol.models import RiskTier, ApprovalToken


class VoiceApprovalDisallowedError(PermissionError):
    """Raised when an attempt is made to authorize T2/T3 operations via voice."""
    pass


class ApprovalRequest(BaseModel):
    """Pending authorization request staged for human operator review."""
    request_id: str
    task_id: str
    action_type: str
    risk_tier: RiskTier
    payload_summary: str
    payload_hash: str
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    status: str = "PENDING"  # "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED"


class ApprovalManager:
    """Coordinates staged action approvals across Gateway and Web Clients."""

    def __init__(self, token_ttl_seconds: float = 300.0):
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._approved_tokens: Dict[str, ApprovalToken] = {}
        self.token_ttl_seconds = token_ttl_seconds

    def create_request(
        self,
        task_id: str,
        action_type: str,
        risk_tier: RiskTier,
        payload_text: str,
    ) -> ApprovalRequest:
        """Stages an action requiring operator approval."""
        req_id = f"appr_{uuid.uuid4().hex[:12]}"
        now = time.time()
        payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()

        req = ApprovalRequest(
            request_id=req_id,
            task_id=task_id,
            action_type=action_type,
            risk_tier=risk_tier,
            payload_summary=payload_text[:1000],
            payload_hash=payload_hash,
            created_at=now,
            expires_at=now + self.token_ttl_seconds,
            status="PENDING",
        )
        self._pending_requests[req_id] = req
        return req

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Returns all unexpired, pending approval requests."""
        now = time.time()
        active = []
        for req in self._pending_requests.values():
            if req.status == "PENDING" and req.expires_at > now:
                active.append(req)
            elif req.status == "PENDING" and req.expires_at <= now:
                req.status = "EXPIRED"
        return active

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Retrieves a specific request by ID."""
        return self._pending_requests.get(request_id)

    def resolve_decision(
        self,
        request_id: str,
        decision: str,
        channel: str,
    ) -> Optional[ApprovalToken]:
        """Resolves an approval decision, strictly enforcing the M-01 screen-button boundary."""
        req = self._pending_requests.get(request_id)
        if not req:
            raise KeyError(f"Approval request '{request_id}' not found.")

        now = time.time()
        if now > req.expires_at:
            req.status = "EXPIRED"
            raise TimeoutError(f"Approval request '{request_id}' has expired.")

        # Rejection handling
        if decision.upper() == "REJECT":
            req.status = "REJECTED"
            return None

        # Approval handling
        if decision.upper() == "APPROVE":
            # M-01 INVARIANT: Voice cannot grant approval for T2 or T3 operations!
            if req.risk_tier in (RiskTier.T2, RiskTier.T3):
                if channel.upper() != "SCREEN_BUTTON":
                    raise VoiceApprovalDisallowedError(
                        f"VOICE_APPROVAL_DISALLOWED: Operations with risk tier {req.risk_tier.value} "
                        "cannot be approved via voice. Explicit on-screen button confirmation is mandatory."
                    )

            # Issue cryptographic ApprovalToken
            token_id = f"token_{uuid.uuid4().hex[:16]}"
            token = ApprovalToken(
                token_id=token_id,
                task_id=req.task_id,
                action_type=req.action_type,
                risk_tier=req.risk_tier,
                payload_hash=req.payload_hash,
                granted_at=now,
                granted_by="SCREEN_BUTTON",
                expires_at=now + self.token_ttl_seconds,
            )

            req.status = "APPROVED"
            self._approved_tokens[token_id] = token
            return token

        raise ValueError(f"Unknown decision '{decision}'. Expected 'APPROVE' or 'REJECT'.")

    def get_token(self, token_id: str) -> Optional[ApprovalToken]:
        """Fetches an active approval token."""
        return self._approved_tokens.get(token_id)


# Global singleton instance
global_approval_manager = ApprovalManager()

