"""Unit Tests for Scoped Vault Client and Secret Masking."""

import pytest
from igris_vault.client import ScopedVaultClient


def test_vault_scoped_retrieval():
    vault = ScopedVaultClient()
    vault.set_project_secrets("acme", "web", {"API_KEY": "acme_live_secret_12345"})
    vault.set_project_secrets("fintech", "core", {"API_KEY": "fintech_live_secret_67890"})

    # Fetch acme secrets
    acme_secrets = vault.fetch_scoped_secrets("acme", "web")
    assert acme_secrets["API_KEY"] == "acme_live_secret_12345"

    # Redaction pattern registered
    patterns = vault.get_redaction_patterns()
    assert "acme_API_KEY" in patterns
    assert patterns["acme_API_KEY"] == "acme_live_secret_12345"

    # Fetching fintech does not leak into acme
    fintech_secrets = vault.fetch_scoped_secrets("fintech", "core")
    assert fintech_secrets["API_KEY"] == "fintech_live_secret_67890"


def test_vault_repr_masks_secrets():
    vault = ScopedVaultClient()
    vault.set_project_secrets("acme", "web", {"DB_PASS": "super_secret_pw"})
    repr_str = repr(vault)
    assert "super_secret_pw" not in repr_str
    assert "Credentials masked" in repr_str

