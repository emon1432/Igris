"""Evaluation Case M-01: Voice Approval Boundary.

Evaluation Objective:
Verify that voice commands (STT utterances like 'Yes', 'Confirm', 'Approved', 'Go ahead')
can NEVER satisfy the authorization requirements for T2 or T3 operations.
Vocal mis-hearing risks necessitate that T2 and T3 actions require physical screen button interaction.
"""

import pytest
from igris_protocol.models import RiskTier
from igris.remote.approval_manager import ApprovalManager, VoiceApprovalDisallowedError
from igris_policy.engine import evaluate_policy
from igris_protocol.models import TaskMode, ClientScope


def test_m01_voice_cannot_approve_t2_staging_deploy():
    """Voice saying 'yes' cannot authorize T2 deployment."""
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="task_m01_t2",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_text="staging diff payload",
    )

    with pytest.raises(VoiceApprovalDisallowedError) as exc_info:
        mgr.resolve_decision(req.request_id, decision="APPROVE", channel="VOICE")

    assert "VOICE_APPROVAL_DISALLOWED" in str(exc_info.value)


def test_m01_screen_button_approves_t2_staging_deploy():
    """Screen button click authorizes T2 deployment and generates a valid token."""
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="task_m01_t2_btn",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_text="staging diff payload",
    )

    token = mgr.resolve_decision(req.request_id, decision="APPROVE", channel="SCREEN_BUTTON")
    assert token is not None
    assert token.granted_by == "SCREEN_BUTTON"

    # Verify that PolicyEngine accepts this token
    scope = ClientScope(client_id="acme", project_id="web")
    decision = evaluate_policy(
        action_name="deploy_staging",
        mode=TaskMode.WORK,
        scope=scope,
        approval_token=token,
    )
    assert decision.allowed is True


def test_m01_voice_cannot_approve_t3_production_push():
    """Voice saying 'yes' cannot authorize T3 production push."""
    mgr = ApprovalManager()
    req = mgr.create_request(
        task_id="task_m01_t3",
        action_type="deploy_production",
        risk_tier=RiskTier.T3,
        payload_text="production release payload",
    )

    with pytest.raises(VoiceApprovalDisallowedError) as exc_info:
        mgr.resolve_decision(req.request_id, decision="APPROVE", channel="VOICE")

    assert "VOICE_APPROVAL_DISALLOWED" in str(exc_info.value)


def test_m01_voice_can_initiate_t0_screen_qa():
    """Voice can initiate T0 conversational and screen Q&A tasks without tokens."""
    scope = ClientScope(client_id="acme", project_id="web")
    decision = evaluate_policy(
        action_name="screen_inspect",
        mode=TaskMode.CONVERSATIONAL,
        scope=scope,
        approval_token=None,
    )
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T0
