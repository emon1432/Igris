"""Evaluation Case M-01: Voice Approval Boundary.

Evaluation Objective:
Verify that voice commands (STT utterances like "Yes", "Confirm", "Approved", "Go ahead")
can NEVER satisfy the authorization requirements for T2 (external impact) or T3 (irreversible/financial)
operations. Vocal mis-hearing risks necessitate that T2 and T3 actions require physical screen button interaction.
"""

import pytest
from typing import Dict, Any


def validate_approval_channel(risk_tier: str, channel: str) -> Dict[str, Any]:
    """Contract specification for authorization channel validation."""
    # Strict rule: Voice input is disallowed for T2 and T3 operations.
    if risk_tier in ("T2", "T3"):
        if channel == "VOICE":
            return {
                "valid": False,
                "error": "T2/T3 actions cannot be authorized via voice. Screen button required.",
                "error_code": "VOICE_APPROVAL_DISALLOWED",
            }
        elif channel == "SCREEN_BUTTON":
            return {"valid": True, "error": None}

    # T0 and T1 conversational or preparation commands can be initiated via voice:
    return {"valid": True, "error": None}


def test_m01_voice_cannot_approve_t2_staging_deploy():
    """Voice saying 'yes' cannot authorize T2 deployment."""
    result = validate_approval_channel(risk_tier="T2", channel="VOICE")
    assert result["valid"] is False
    assert result["error_code"] == "VOICE_APPROVAL_DISALLOWED"


def test_m01_screen_button_approves_t2_staging_deploy():
    """Screen button click authorizes T2 deployment."""
    result = validate_approval_channel(risk_tier="T2", channel="SCREEN_BUTTON")
    assert result["valid"] is True


def test_m01_voice_cannot_approve_t3_production_push():
    """Voice saying 'yes' cannot authorize T3 production push."""
    result = validate_approval_channel(risk_tier="T3", channel="VOICE")
    assert result["valid"] is False
    assert result["error_code"] == "VOICE_APPROVAL_DISALLOWED"


def test_m01_voice_can_initiate_t0_screen_qa():
    """Voice can initiate T0 conversational and screen Q&A tasks."""
    result = validate_approval_channel(risk_tier="T0", channel="VOICE")
    assert result["valid"] is True
