"""Evaluation Case P-01: Approval Gate Enforcement.

Evaluation Objective:
Verify that the production Policy Engine deterministically blocks any T2 or T3 tool invocation
unless an explicit, unexpired ApprovalToken granted via SCREEN_BUTTON is provided.
Voice commands or implicit approvals must be strictly rejected.
"""

import pytest
from igris_protocol.models import RiskTier, TaskMode, ClientScope, ApprovalToken
from igris_policy.engine import evaluate_policy


@pytest.fixture
def sample_scope():
    return ClientScope(client_id="acme", project_id="web")


def test_p01_t0_read_action_allowed_without_approval(sample_scope):
    """T0 read-only operations do not require screen button approval."""
    decision = evaluate_policy("read_email", mode=TaskMode.TRIAGE, scope=sample_scope, approval_token=None)
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T0


def test_p01_t1_local_reversible_action_allowed(sample_scope):
    """T1 operations in branch sandbox do not require screen button approval."""
    decision = evaluate_policy("git_branch_commit", mode=TaskMode.WORK, scope=sample_scope, approval_token=None)
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T1


def test_p01_t2_staging_deploy_blocked_without_screen_approval(sample_scope):
    """T2 staging deployment must be blocked without on-screen button approval."""
    decision = evaluate_policy("deploy_staging", mode=TaskMode.WORK, scope=sample_scope, approval_token=None)
    assert decision.allowed is False
    assert decision.error_code == "APPROVAL_REQUIRED"


def test_p01_t2_voice_approval_fails_to_authorize(sample_scope):
    """Vocal agreement ('Yes, deploy staging') cannot authorize T2 operations."""
    voice_token = ApprovalToken(
        token_id="tok_voice",
        task_id="task_1",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_hash="dummy_hash",
        granted_at=100.0,
        granted_by="VOICE",
        expires_at=500.0,
    )
    decision = evaluate_policy("deploy_staging", mode=TaskMode.WORK, scope=sample_scope, approval_token=voice_token)
    assert decision.allowed is False
    assert decision.error_code == "VOICE_APPROVAL_DISALLOWED"


def test_p01_t3_client_email_blocked_without_screen_approval(sample_scope):
    """T3 client communications must be blocked without on-screen button approval."""
    decision = evaluate_policy("send_client_email", mode=TaskMode.WORK, scope=sample_scope, approval_token=None)
    assert decision.allowed is False
    assert decision.error_code == "APPROVAL_REQUIRED"


def test_p01_t3_client_email_permitted_with_screen_button_approval(sample_scope):
    """T3 client communications succeed when explicit on-screen button approval is granted."""
    screen_token = ApprovalToken(
        token_id="tok_screen",
        task_id="task_1",
        action_type="send_client_email",
        risk_tier=RiskTier.T3,
        payload_hash="valid_hash_123",
        granted_at=100.0,
        granted_by="SCREEN_BUTTON",
        expires_at=500.0,
    )
    decision = evaluate_policy(
        "send_client_email",
        mode=TaskMode.WORK,
        scope=sample_scope,
        approval_token=screen_token,
        current_time=150.0,
        payload_hash="valid_hash_123",
    )
    assert decision.allowed is True
    assert decision.error_code is None
