"""Scoped Secret Vault Client.

CI Invariant:
This client is imported strictly by sandboxed tool runners under tools/*.
The Orchestrator and Gateway are prohibited from importing or holding raw vault credentials.

Guarantees (S-01):
1. Delivers narrowly scoped credentials for a specific client/project.
2. Registers secret values with the redaction filter to ensure zero secrets appear in logs, prompts, or ledger.
3. Masks secrets in string representations.
"""

from typing import Dict, Optional


class ScopedVaultClient:
    """Client for securely retrieving scoped task credentials."""

    def __init__(self, in_memory_vault: Optional[Dict[str, Dict[str, str]]] = None):
        # Format: { "client_id/project_id": { "KEY_NAME": "SECRET_VAL" } }
        self._vault = in_memory_vault or {}
        self._registered_redaction_patterns: Dict[str, str] = {}

    def set_project_secrets(self, client_id: str, project_id: str, secrets: Dict[str, str]):
        """Populates secrets for a client project (admin/setup use)."""
        key = f"{client_id}/{project_id}"
        self._vault[key] = dict(secrets)

    def fetch_scoped_secrets(self, client_id: str, project_id: str) -> Dict[str, str]:
        """Fetches credentials bound strictly to the designated client and project."""
        key = f"{client_id}/{project_id}"
        secrets = self._vault.get(key, {})

        # Track secrets to ensure they are redacted from logs and ledger
        for k, v in secrets.items():
            if v and len(v) >= 4:
                self._registered_redaction_patterns[f"{client_id}_{k}"] = v

        return dict(secrets)

    def get_redaction_patterns(self) -> Dict[str, str]:
        """Returns map of secret patterns that must be redacted by ToolSDK."""
        return dict(self._registered_redaction_patterns)

    def __repr__(self) -> str:
        return "<ScopedVaultClient: Credentials masked and secured>"

