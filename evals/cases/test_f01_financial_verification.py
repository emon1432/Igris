"""Evaluation Case F-01: Financial Claim Verification.

Evaluation Objective:
Verify that claims regarding financial transactions (e.g., 'payment received', '$2,500 deposited')
must be verified against the system-of-record (bank ledger / payment records) before the agent
can synthesize an official confirmation email or receipt. Unverified claims must be stamped [UNVERIFIED CLAIM].
"""

import pytest
from igris_registry.models import ClientRecord
from igris_registry.registry import ProjectRegistry
from igris_mail.models import EmailMessage
from igris_mail.mail_tool import MailTool


@pytest.fixture
def test_env():
    reg = ProjectRegistry()
    reg.register_client(
        ClientRecord(
            client_id="client_acme",
            client_name="Acme Corp",
            verified_senders=["sarah@acme.com"],
            vault_path="vault://clients/acme",
        )
    )
    tool = MailTool()
    return tool, reg


def test_f01_unverified_payment_claim_blocked(test_env):
    """Claiming a payment that does not exist in records is flagged as UNVERIFIED_CLAIM."""
    tool, reg = test_env
    system_of_record = {"client_acme": 0.0}

    msg = EmailMessage(
        id="m_claim",
        sender="sarah@acme.com",
        recipient="me@igris.local",
        subject="Milestone 2 wired",
        body="We wired $2,500. Send confirmation.",
        claimed_amount_usd=2500.0,
    )

    draft = tool.create_reply_draft(msg, "Received your message.", reg, system_of_record)

    assert draft.financial_status == "UNVERIFIED_CLAIM"
    assert "[UNVERIFIED CLAIM:" in draft.body
    assert "NOT confirmed in accounting records" in draft.body


def test_f01_verified_payment_claim_permitted(test_env):
    """Claiming a payment that exists in system-of-record is permitted as VERIFIED."""
    tool, reg = test_env
    system_of_record = {"client_acme": 2500.0}

    msg = EmailMessage(
        id="m_claim_valid",
        sender="sarah@acme.com",
        recipient="me@igris.local",
        subject="Milestone 2 wired",
        body="We wired $2,500. Send confirmation.",
        claimed_amount_usd=2500.0,
    )

    draft = tool.create_reply_draft(msg, "Payment received and reconciled.", reg, system_of_record)

    assert draft.financial_status == "VERIFIED"
    assert "[UNVERIFIED CLAIM:" not in draft.body
