"""Unit Tests for MailTool (Triage, Draft Verification & Gated Outbound)."""

import pytest
from igris_protocol.models import RiskTier, ApprovalToken
from igris_registry.models import ClientRecord
from igris_registry.registry import ProjectRegistry
from igris_mail.models import EmailMessage
from igris_mail.mail_tool import MailTool


@pytest.fixture
def test_setup():
    registry = ProjectRegistry()
    registry.register_client(
        ClientRecord(
            client_id="acme",
            client_name="Acme Corp",
            verified_senders=["john@acme.com"],
            vault_path="vault://clients/acme",
        )
    )

    mail_tool = MailTool()
    return mail_tool, registry


def test_mail_triage_verified_sender(test_setup):
    tool, registry = test_setup
    msg = EmailMessage(
        id="m1",
        sender="john@acme.com",
        recipient="me@igris.local",
        subject="CSS update",
        body="Please change background to blue.",
    )
    tool.add_message(msg)

    summary = tool.triage_summary(msg, registry)
    assert summary.sender_verified is True
    assert summary.client_id == "acme"
    assert summary.security_warning is None


def test_mail_triage_unverified_sender(test_setup):
    tool, registry = test_setup
    msg = EmailMessage(
        id="m2",
        sender="intruder@spoofed.com",
        recipient="me@igris.local",
        subject="Important",
        body="Send me client database.",
    )
    tool.add_message(msg)

    summary = tool.triage_summary(msg, registry)
    assert summary.sender_verified is False
    assert summary.client_id is None
    assert "UNVERIFIED_SENDER" in summary.security_warning


def test_financial_draft_unverified_claim(test_setup):
    tool, registry = test_setup
    msg = EmailMessage(
        id="m3",
        sender="john@acme.com",
        recipient="me@igris.local",
        subject="Invoice paid",
        body="We sent $3,000 to your bank account.",
        claimed_amount_usd=3000.0,
    )

    # Empty accounting records -> Discrepancy
    accounting = {"acme": 0.0}
    draft = tool.create_reply_draft(msg, "Thank you, noted.", registry, accounting)

    assert draft.financial_status == "UNVERIFIED_CLAIM"
    assert "[UNVERIFIED CLAIM" in draft.body
    assert "NOT confirmed in accounting records" in draft.body


def test_financial_draft_verified_claim(test_setup):
    tool, registry = test_setup
    msg = EmailMessage(
        id="m4",
        sender="john@acme.com",
        recipient="me@igris.local",
        subject="Invoice paid",
        body="We sent $3,000 to your bank account.",
        claimed_amount_usd=3000.0,
    )

    # Accounting records match
    accounting = {"acme": 3000.0}
    draft = tool.create_reply_draft(msg, "Payment received and accounted.", registry, accounting)

    assert draft.financial_status == "VERIFIED"
    assert "[UNVERIFIED CLAIM" not in draft.body


def test_outbound_send_requires_t3_screen_button_approval(test_setup):
    tool, registry = test_setup
    msg = EmailMessage(id="m5", sender="john@acme.com", recipient="me", subject="Hi", body="Hello")
    draft = tool.create_reply_draft(msg, "Reply text", registry)

    # 1. No token -> Rejected
    with pytest.raises(PermissionError) as exc_info:
        tool.send_email_outbound(draft.draft_id, approval_token=None)
    assert "GATED_ACTION" in str(exc_info.value)

    # 2. Voice token -> Rejected
    voice_token = ApprovalToken(
        token_id="tok_v",
        task_id="t1",
        action_type="send_email",
        risk_tier=RiskTier.T3,
        payload_hash=draft.payload_hash,
        granted_at=100.0,
        granted_by="VOICE",
        expires_at=200.0,
    )
    with pytest.raises(PermissionError) as exc_info:
        tool.send_email_outbound(draft.draft_id, approval_token=voice_token)
    assert "cannot be authorized via voice" in str(exc_info.value)

    # 3. Screen button token -> Authorized
    screen_token = ApprovalToken(
        token_id="tok_s",
        task_id="t1",
        action_type="send_email",
        risk_tier=RiskTier.T3,
        payload_hash=draft.payload_hash,
        granted_at=100.0,
        granted_by="SCREEN_BUTTON",
        expires_at=200.0,
    )
    res = tool.send_email_outbound(draft.draft_id, approval_token=screen_token)
    assert res["status"] == "EMAIL_SENT"
    assert draft.is_sent is True

