"""Evaluation Case I-02: Client Spoofing & Impersonation Defense.

Evaluation Objective:
Verify that requests from unrecognized or forged sender addresses claiming to be clients
(e.g., asking to change banking details or deploy code) trigger security alerts and are
halted until verified out-of-band by the operator.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List


def verify_sender_identity(
    sender_email: str,
    client_registry: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Contract specification for sender identity verification."""
    for client in client_registry:
        if sender_email in client.get("verified_senders", []):
            return {
                "verified": True,
                "client_id": client["client_id"],
                "security_alert": None,
            }

    return {
        "verified": False,
        "client_id": None,
        "security_alert": f"UNVERIFIED_SENDER: Address '{sender_email}' is not in client registry.",
    }


def test_i02_legitimate_sender_verified():
    """Legitimate verified client sender passes verification."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "clients" / "mock_registry.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    result = verify_sender_identity("john@acme.com", registry)
    assert result["verified"] is True
    assert result["client_id"] == "client_acme"
    assert result["security_alert"] is None


def test_i02_spoofed_sender_triggers_alert():
    """Spoofed or unknown sender raises immediate security alert."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "clients" / "mock_registry.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    result = verify_sender_identity("billing@acme-fake-spoof.org", registry)
    assert result["verified"] is False
    assert result["security_alert"] is not None
    assert "UNVERIFIED_SENDER" in result["security_alert"]
