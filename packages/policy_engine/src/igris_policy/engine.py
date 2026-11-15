"""Deterministic Pure-Code Policy Engine.

CI Invariant:
This module contains ZERO imports of LLM SDKs, network libraries, or file system I/O.
It implements deterministic pure functions that validate operations against:
1. Operational Mode (TRIAGE vs WORK vs CONVERSATIONAL)
2. Risk Tier Hierarchy (T0 to T3)
3. Cryptographic Screen-Button Approval Tokens
4. Client Scoping
"""

from typing import Optional, Dict, Any
from igris_protocol.models import RiskTier, TaskMode, ClientScope, ApprovalToken


# Standardized tool risk classification table
TOOL_RISK_MAP: Dict[str, RiskTier] = {
    # T0: Read-Only
    "read_email": RiskTier.T0,
    "search_repo": RiskTier.T0,
    "view_diff": RiskTier.T0,
    "fetch_report": RiskTier.T0,
    "screen_inspect": RiskTier.T0,
    "synthesize_draft_data": RiskTier.T0,

    # T1: Local / Reversible mutations in branch/sandbox
    "git_branch_commit": RiskTier.T1,
    "write_local_draft": RiskTier.T1,
    "run_tests": RiskTier.T1,
    "create_note": RiskTier.T1,
    "write_file": RiskTier.T1,

    # T2: External impact, staging deployments, non-client outbound
    "deploy_staging": RiskTier.T2,
    "forward_note": RiskTier.T2,
    "post_external_webhook": RiskTier.T2,

    # T3: Irreversible, production, client-facing, financial, data destruction
    "deploy_production": RiskTier.T3,
    "send_email": RiskTier.T3,
    "send_client_email": RiskTier.T3,
    "send_client_message": RiskTier.T3,
    "delete_data": RiskTier.T3,
    "execute_destructive_bash": RiskTier.T3,
    "confirm_financial_payment": RiskTier.T3,
}


class PolicyDecision:
    """Outcome of a deterministic policy evaluation."""

    def __init__(
        self,
        allowed: bool,
        reason: str,
        error_code: Optional[str] = None,
        risk_tier: Optional[RiskTier] = None,
    ):
        self.allowed = allowed
        self.reason = reason
        self.error_code = error_code
        self.risk_tier = risk_tier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "error_code": self.error_code,
            "risk_tier": self.risk_tier.value if self.risk_tier else None,
        }

    def __repr__(self) -> str:
        return f"PolicyDecision(allowed={self.allowed}, error_code={self.error_code}, tier={self.risk_tier})"


def get_tool_risk_tier(action_name: str, explicit_tier: Optional[RiskTier] = None) -> RiskTier:
    """Resolves the risk tier for a tool invocation."""
    if explicit_tier:
        return explicit_tier
    return TOOL_RISK_MAP.get(action_name, RiskTier.T3)  # Fail-closed default: T3 for unknown tools


def evaluate_policy(
    action_name: str,
    mode: TaskMode,
    scope: Optional[ClientScope] = None,
    approval_token: Optional[ApprovalToken] = None,
    current_time: float = 0.0,
    explicit_tier: Optional[RiskTier] = None,
    payload_hash: Optional[str] = None,
) -> PolicyDecision:
    """Pure deterministic policy evaluation function.

    Guarantees:
    - P-01: T2/T3 blocked without valid ApprovalToken granted via SCREEN_BUTTON.
    - P-02: TRIAGE mode strictly permits only T0 read-only tools.
    - M-01: Voice approval is strictly rejected for T2/T3.
    """
    risk_tier = get_tool_risk_tier(action_name, explicit_tier)

    # 1. Operational Mode Boundary Check
    if mode == TaskMode.TRIAGE:
        # In Triage Mode, ONLY T0 read-only tools are allowed.
        if risk_tier != RiskTier.T0:
            return PolicyDecision(
                allowed=False,
                reason=f"Action '{action_name}' with risk tier {risk_tier.value} is strictly forbidden in TRIAGE mode.",
                error_code="FORBIDDEN_TOOL_IN_MODE",
                risk_tier=risk_tier,
            )

    elif mode == TaskMode.CONVERSATIONAL:
        # In Conversational mode, only T0 screen inspection or chat dialogue is allowed.
        if risk_tier != RiskTier.T0:
            return PolicyDecision(
                allowed=False,
                reason=f"Mutating action '{action_name}' cannot be invoked in CONVERSATIONAL mode.",
                error_code="CONVERSATIONAL_MODE_DISALLOWS_MUTATION",
                risk_tier=risk_tier,
            )

    elif mode == TaskMode.WORK:
        # In Work Mode, client scope is mandatory
        if scope is None:
            return PolicyDecision(
                allowed=False,
                reason="Work mode operations require an explicit ClientScope.",
                error_code="MISSING_PROJECT_SCOPE",
                risk_tier=risk_tier,
            )

    # 2. Risk Tier Hierarchy Evaluation
    if risk_tier in (RiskTier.T0, RiskTier.T1):
        # T0 and T1 are locally contained and permitted
        return PolicyDecision(
            allowed=True,
            reason=f"{risk_tier.value} action permitted under policy.",
            error_code=None,
            risk_tier=risk_tier,
        )

    # 3. T2 and T3 External / Irreversible Enforcement
    if risk_tier in (RiskTier.T2, RiskTier.T3):
        if approval_token is None:
            return PolicyDecision(
                allowed=False,
                reason=f"{risk_tier.value} action '{action_name}' requires explicit on-screen button approval.",
                error_code="APPROVAL_REQUIRED",
                risk_tier=risk_tier,
            )

        # Check approval channel (Must be physical SCREEN_BUTTON; VOICE is invalid)
        if approval_token.granted_by != "SCREEN_BUTTON":
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Approval channel '{approval_token.granted_by}' is invalid. "
                    f"{risk_tier.value} approvals are strictly restricted to physical SCREEN_BUTTON clicks."
                ),
                error_code="VOICE_APPROVAL_DISALLOWED",
                risk_tier=risk_tier,
            )

        # Check token expiration
        if current_time > 0 and approval_token.is_expired(current_time):
            return PolicyDecision(
                allowed=False,
                reason=f"Approval token '{approval_token.token_id}' has expired.",
                error_code="APPROVAL_TOKEN_EXPIRED",
                risk_tier=risk_tier,
            )

        # For T3: Payload verification (payload hash must match or be non-empty)
        if risk_tier == RiskTier.T3:
            if not approval_token.payload_hash or len(approval_token.payload_hash.strip()) == 0:
                return PolicyDecision(
                    allowed=False,
                    reason="T3 operations require an approval token with an explicit payload hash.",
                    error_code="MISSING_PAYLOAD_PROOF_HASH",
                    risk_tier=risk_tier,
                )
            if payload_hash and approval_token.payload_hash != payload_hash:
                return PolicyDecision(
                    allowed=False,
                    reason="Payload hash discrepancy: approval token hash does not match current payload.",
                    error_code="PAYLOAD_HASH_MISMATCH",
                    risk_tier=risk_tier,
                )

        return PolicyDecision(
            allowed=True,
            reason=f"{risk_tier.value} action successfully verified with approval token.",
            error_code=None,
            risk_tier=risk_tier,
        )

    return PolicyDecision(
        allowed=False,
        reason="Unknown risk tier evaluation error.",
        error_code="UNKNOWN_POLICY_STATE",
        risk_tier=risk_tier,
    )

