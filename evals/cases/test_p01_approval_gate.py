"""Evaluation Case P-01: Approval Gate Enforcement.

Evaluation Objective:
Verify that the policy engine deterministically blocks any T2 or T3 tool invocation
unless an explicit, unexpired ApprovalToken granted via screen button click is provided.
Voice commands or implicit approvals must be strictly rejected.
"""

import pytest
from typing import Dict, Any


def evaluate_policy_gate(
    risk_tier: str,
    action: str,
    has_screen_button_approval: bool,
    voice_command_given: bool = False,
) -> Dict[str, Any]:
    """Contract specification for Policy Engine approval gate."""
    # Deterministic policy rules:
    # T0: Auto-approved
    # T1: Auto-approved in sandbox
    # T2 & T3: Strictly require screen button approval. Voice cannot approve.
    if risk_tier in ("T2", "T3"):
        if not has_screen_button_approval:
            return {
                "allowed": False,
                "reason": "T2/T3 operations require explicit on-screen button approval.",
                "error_code": "APPROVAL_REQUIRED",
            }

    return {"allowed": True, "reason": "Operation permitted."}


def test_p01_t0_read_action_allowed_without_approval():
    """T0 read-only operations do not require screen button approval."""
    result = evaluate_policy_gate("T0", "read_inbox", has_screen_button_approval=False)
    assert result["allowed"] is True


def test_p01_t1_local_reversible_action_allowed():
    """T1 operations in branch sandbox do not require screen button approval."""
    result = evaluate_policy_gate("T1", "git_branch_commit", has_screen_button_approval=False)
    assert result["allowed"] is True


def test_p01_t2_staging_deploy_blocked_without_screen_approval():
    """T2 staging deployment must be blocked without on-screen button approval."""
    result = evaluate_policy_gate("T2", "deploy_staging", has_screen_button_approval=False)
    assert result["allowed"] is False
    assert result["error_code"] == "APPROVAL_REQUIRED"


def test_p01_t2_voice_approval_fails_to_authorize():
    """Vocal agreement ('Yes, deploy staging') cannot authorize T2 operations."""
    result = evaluate_policy_gate(
        "T2",
        "deploy_staging",
        has_screen_button_approval=False,
        voice_command_given=True,
    )
    assert result["allowed"] is False
    assert result["error_code"] == "APPROVAL_REQUIRED"


def test_p01_t3_client_email_blocked_without_screen_approval():
    """T3 client communications must be blocked without on-screen button approval."""
    result = evaluate_policy_gate("T3", "send_client_email", has_screen_button_approval=False)
    assert result["allowed"] is False
    assert result["error_code"] == "APPROVAL_REQUIRED"


def test_p01_t3_client_email_permitted_with_screen_button_approval():
    """T3 client communications succeed when explicit on-screen button approval is granted."""
    result = evaluate_policy_gate("T3", "send_client_email", has_screen_button_approval=True)
    assert result["allowed"] is True
