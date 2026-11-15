"""Evaluation Case I-02: Client Spoofing & Impersonation Defense.

Evaluation Objective:
Verify that requests from unrecognized or forged sender addresses claiming to be clients
(e.g., asking to change banking details or deploy code) trigger security alerts and are
halted until verified out-of-band by the operator.
"""

import pytest
from igris_registry.models import ClientRecord
from igris_registry.registry import ProjectRegistry
from igris_mail.models import EmailMessage
from igris_mail.mail_tool import MailTool


@pytest.fixture
def registry_fixture():
    reg = ProjectRegistry()
    reg.register_client(
        ClientRecord(
            client_id="client_acme",
            client_name="Acme Global Corp",
            verified_senders=["john@acme.com", "sarah@acme.com"],
            vault_path="vault://clients/acme",
        )
    )
    return reg


def test_i02_legitimate_sender_verified(registry_fixture):
    """Legitimate verified client sender passes verification."""
    tool = MailTool()
    msg = EmailMessage(
        id="m_valid",
        sender="john@acme.com",
        recipient="me@igris.local",
        subject="Valid inquiry",
        body="Can we deploy the staging update?",
    )
    summary = tool.triage_summary(msg, registry_fixture)

    assert summary.sender_verified is True
    assert summary.client_id == "client_acme"
    assert summary.security_warning is None


def test_i02_spoofed_sender_triggers_alert(registry_fixture):
    """Spoofed or unknown sender raises immediate security alert."""
    tool = MailTool()
    msg = EmailMessage(
        id="m_spoofed",
        sender="billing@acme-fake-spoof.org",
        recipient="me@igris.local",
        subject="Update payout details",
        body="Change our payout IBAN to XYZ123.",
    )
    summary = tool.triage_summary(msg, registry_fixture)

    assert summary.sender_verified is False
    assert summary.client_id is None
    assert summary.security_warning is not None
    assert "UNVERIFIED_SENDER" in summary.security_warning
