"""Evaluation Case S-01: Vault Secret Isolation.

Evaluation Objective:
Verify that raw credentials, API keys, and database tokens retrieved from the vault
are injected solely into sandboxed tool runners and are strictly redacted from:
1. LLM context prompts
2. Action ledger records
3. Agent scratchpad logs
4. User-facing outputs and diffs
"""

import pytest
import re
from typing import Dict, Any


def sanitize_output(raw_text: str, secret_patterns: Dict[str, str]) -> str:
    """Contract specification for secret redaction filter."""
    sanitized = raw_text
    for secret_name, secret_val in secret_patterns.items():
        if secret_val:
            sanitized = sanitized.replace(secret_val, f"[REDACTED_SECRET_{secret_name.upper()}]")
    return sanitized


def test_s01_secret_redacted_from_log_and_ledger():
    """Confidential tokens must be redacted from execution outputs before storage."""
    secrets = {
        "stripe_key": "mock_stripe_key_val_998877",
        "db_password": "super_secret_db_password_123!",
    }

    raw_command_output = (
        "Connecting to database with password super_secret_db_password_123! ... "
        "Configured Stripe billing key mock_stripe_key_val_998877 successfully."
    )

    clean_output = sanitize_output(raw_command_output, secrets)

    assert "mock_stripe_key_val_998877" not in clean_output
    assert "super_secret_db_password_123!" not in clean_output
    assert "[REDACTED_SECRET_STRIPE_KEY]" in clean_output
    assert "[REDACTED_SECRET_DB_PASSWORD]" in clean_output
