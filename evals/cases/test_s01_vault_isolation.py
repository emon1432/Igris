"""Evaluation Case S-01: Vault Secret Isolation.

Evaluation Objective:
Verify that raw credentials and tokens fetched from the ScopedVaultClient:
1. Are injected solely into sandboxed tool runners.
2. Are automatically registered for redaction and redacted from ledger entries and tool outputs.
3. Never appear in LLM context, logs, or reports.
"""

import pytest
from igris_protocol.models import TaskMode
from igris_vault.client import ScopedVaultClient
from igris_tool_sdk.wrapper import SecureToolSDK


def test_s01_vault_secrets_redacted_from_ledger():
    """Secrets fetched by tool runner must be redacted from ledger records."""
    vault = ScopedVaultClient()
    vault.set_project_secrets("acme", "web", {
        "STRIPE_KEY": "mock_stripe_key_val_998877",
        "DB_PASS": "ultra_secret_db_pass_9988",
    })

    # Retrieve scoped secrets (auto-registers redaction patterns)
    secrets = vault.fetch_scoped_secrets("acme", "web")
    sdk = SecureToolSDK(secrets_to_redact=vault.get_redaction_patterns())

    # Simulated tool runner that outputs connection info containing the secret
    def tool_connecting_to_db():
        return f"Connected to DB with {secrets['DB_PASS']} and configured Stripe {secrets['STRIPE_KEY']}"

    result = sdk.invoke(
        action_name="read_email",
        tool_fn=tool_connecting_to_db,
        task_id="task_secret_test",
        mode=TaskMode.TRIAGE,
        input_parameters={},
    )

    # Check ledger entry
    latest_entry = sdk.ledger.get_all_entries()[-1]
    assert "mock_stripe_key_val_998877" not in latest_entry.output_summary
    assert "ultra_secret_db_pass_9988" not in latest_entry.output_summary
    assert "[REDACTED_ACME_STRIPE_KEY]" in latest_entry.output_summary
    assert "[REDACTED_ACME_DB_PASS]" in latest_entry.output_summary
