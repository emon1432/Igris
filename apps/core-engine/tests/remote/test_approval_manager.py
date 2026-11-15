"""Unit Tests for ApprovalManager and Voice Approval Boundary (M-01)."""

import pytest
from igris_protocol.models import RiskTier
from igris.remote.approval_manager import ApprovalManager, VoiceApprovalDisallowedError


def test_approval_manager_request_lifecycle():
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="t1",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_text="git diff commit abc1234",
    )
    assert req.status == "PENDING"
    assert req.action_type == "deploy_staging"
    assert req.risk_tier == RiskTier.T2
    assert len(req.payload_hash) == 64

    pending = mgr.get_pending_requests()
    assert len(pending) == 1
    assert pending[0].request_id == req.request_id


def test_approval_manager_m01_voice_disallowed():
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="t2",
        action_type="send_client_email",
        risk_tier=RiskTier.T3,
        payload_text="Payment confirmed",
    )

    # Attempting to authorize via voice MUST raise VoiceApprovalDisallowedError
    with pytest.raises(VoiceApprovalDisallowedError) as exc_info:
        mgr.resolve_decision(req.request_id, decision="APPROVE", channel="VOICE")

    assert "VOICE_APPROVAL_DISALLOWED" in str(exc_info.value)
    assert "cannot be approved via voice" in str(exc_info.value)


def test_approval_manager_screen_button_authorized():
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="t3",
        action_type="deploy_production",
        risk_tier=RiskTier.T3,
        payload_text="Release v1.0.0",
    )

    # Screen button confirmation issues valid ApprovalToken
    token = mgr.resolve_decision(req.request_id, decision="APPROVE", channel="SCREEN_BUTTON")
    assert token is not None
    assert token.risk_tier == RiskTier.T3
    assert token.granted_by == "SCREEN_BUTTON"
    assert token.payload_hash == req.payload_hash

    # Request status updated
    assert req.status == "APPROVED"


def test_approval_manager_rejection():
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="t4",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_text="Some diff",
    )

    token = mgr.resolve_decision(req.request_id, decision="REJECT", channel="SCREEN_BUTTON")
    assert token is None
    assert req.status == "REJECTED"

