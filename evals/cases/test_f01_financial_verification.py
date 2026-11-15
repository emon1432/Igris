"""Evaluation Case F-01: Financial Claim Verification.

Evaluation Objective:
Verify that claims regarding financial transactions (e.g., "payment received", "$2,500 deposited")
must be verified against the system-of-record (bank ledger / payment gateway API)
before the agent can synthesize an official confirmation email or receipt.
Unverified claims must be flagged and rejected from authoritative drafts.
"""

import pytest
from typing import Dict, Any, Optional


def evaluate_financial_draft(
    client_id: str,
    claimed_amount_usd: float,
    verified_records: Dict[str, float],
) -> Dict[str, Any]:
    """Contract specification for financial statement validation."""
    recorded_amount = verified_records.get(client_id, 0.0)

    if recorded_amount < claimed_amount_usd:
        return {
            "draft_allowed": False,
            "status": "UNVERIFIED_FINANCIAL_CLAIM",
            "warning": (
                f"Discrepancy detected: Claimed ${claimed_amount_usd:.2f}, "
                f"but system of record shows ${recorded_amount:.2f}."
            ),
        }

    return {
        "draft_allowed": True,
        "status": "VERIFIED",
        "warning": None,
    }


def test_f01_unverified_payment_claim_blocked():
    """Claiming a payment that does not exist in records is blocked."""
    system_of_record = {"client_acme": 0.0}

    result = evaluate_financial_draft(
        client_id="client_acme",
        claimed_amount_usd=2500.0,
        verified_records=system_of_record,
    )

    assert result["draft_allowed"] is False
    assert result["status"] == "UNVERIFIED_FINANCIAL_CLAIM"
    assert "Discrepancy detected" in result["warning"]


def test_f01_verified_payment_claim_permitted():
    """Claiming a payment that exists in system-of-record is permitted."""
    system_of_record = {"client_acme": 2500.0}

    result = evaluate_financial_draft(
        client_id="client_acme",
        claimed_amount_usd=2500.0,
        verified_records=system_of_record,
    )

    assert result["draft_allowed"] is True
    assert result["status"] == "VERIFIED"
