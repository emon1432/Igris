"""Unit Tests for Policy Engine Pure Functions."""

import time
import pytest
from igris_protocol.models import RiskTier, TaskMode, ClientScope, ApprovalToken
from igris_policy.engine import evaluate_policy, get_tool_risk_tier


def test_t0_tool_allowed_in_triage_mode():
    decision = evaluate_policy("read_email", mode=TaskMode.TRIAGE)
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T0
    assert decision.error_code is None


def test_t1_write_tool_blocked_in_triage_mode():
    decision = evaluate_policy("write_file", mode=TaskMode.TRIAGE)
    assert decision.allowed is False
    assert decision.error_code == "FORBIDDEN_TOOL_IN_MODE"


def test_t3_tool_blocked_in_triage_mode():
    decision = evaluate_policy("send_email", mode=TaskMode.TRIAGE)
    assert decision.allowed is False
    assert decision.error_code == "FORBIDDEN_TOOL_IN_MODE"


def test_conversational_mode_blocks_mutating_actions():
    decision = evaluate_policy("write_file", mode=TaskMode.CONVERSATIONAL)
    assert decision.allowed is False
    assert decision.error_code == "CONVERSATIONAL_MODE_DISALLOWS_MUTATION"


def test_work_mode_requires_client_scope():
    decision = evaluate_policy("write_file", mode=TaskMode.WORK, scope=None)
    assert decision.allowed is False
    assert decision.error_code == "MISSING_PROJECT_SCOPE"


def test_t1_allowed_in_work_mode_with_scope():
    scope = ClientScope(client_id="acme", project_id="web")
    decision = evaluate_policy("write_file", mode=TaskMode.WORK, scope=scope)
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T1


def test_t2_requires_screen_button_approval():
    scope = ClientScope(client_id="acme", project_id="web")
    # No token
    decision = evaluate_policy("deploy_staging", mode=TaskMode.WORK, scope=scope, approval_token=None)
    assert decision.allowed is False
    assert decision.error_code == "APPROVAL_REQUIRED"

    # Token granted via VOICE must fail
    voice_token = ApprovalToken(
        token_id="tok_1",
        task_id="task_1",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_hash="abc",
        granted_at=100.0,
        granted_by="VOICE",
        expires_at=200.0,
    )
    decision = evaluate_policy("deploy_staging", mode=TaskMode.WORK, scope=scope, approval_token=voice_token)
    assert decision.allowed is False
    assert decision.error_code == "VOICE_APPROVAL_DISALLOWED"

    # Token granted via SCREEN_BUTTON succeeds
    screen_token = ApprovalToken(
        token_id="tok_2",
        task_id="task_1",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_hash="abc",
        granted_at=100.0,
        granted_by="SCREEN_BUTTON",
        expires_at=200.0,
    )
    decision = evaluate_policy(
        "deploy_staging",
        mode=TaskMode.WORK,
        scope=scope,
        approval_token=screen_token,
        current_time=150.0,
    )
    assert decision.allowed is True


def test_t3_requires_payload_hash_match():
    scope = ClientScope(client_id="acme", project_id="web")
    token = ApprovalToken(
        token_id="tok_3",
        task_id="task_1",
        action_type="send_client_email",
        risk_tier=RiskTier.T3,
        payload_hash="hash_expected_123",
        granted_at=100.0,
        granted_by="SCREEN_BUTTON",
        expires_at=200.0,
    )

    # Hash mismatch
    decision = evaluate_policy(
        "send_client_email",
        mode=TaskMode.WORK,
        scope=scope,
        approval_token=token,
        current_time=150.0,
        payload_hash="hash_different_456",
    )
    assert decision.allowed is False
    assert decision.error_code == "PAYLOAD_HASH_MISMATCH"

    # Hash match
    decision = evaluate_policy(
        "send_client_email",
        mode=TaskMode.WORK,
        scope=scope,
        approval_token=token,
        current_time=150.0,
        payload_hash="hash_expected_123",
    )
    assert decision.allowed is True

