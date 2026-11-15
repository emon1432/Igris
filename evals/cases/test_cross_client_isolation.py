"""Evaluation Case: Cross-Client Data & Credential Isolation.

Evaluation Objective:
Verify that when executing a task bound to Client A:
1. Accessing Client B's registry metadata raises CrossClientAccessViolationError.
2. Attempting to access files or repositories outside Client A's repo_path is blocked.
3. Fetching credentials for Client B under Client A's task context is forbidden.
"""

import pytest
from igris_registry.models import ClientRecord, ProjectRecord
from igris_registry.registry import ProjectRegistry, CrossClientAccessViolationError
from igris_vault.client import ScopedVaultClient


@pytest.fixture
def isolated_clients_fixture(tmp_path):
    repo_acme = tmp_path / "acme_repo"
    repo_acme.mkdir()
    repo_fintech = tmp_path / "fintech_repo"
    repo_fintech.mkdir()

    registry = ProjectRegistry()
    registry.register_client(
        ClientRecord(
            client_id="client_acme",
            client_name="Acme Corp",
            projects={"web": ProjectRecord(project_id="web", repo_path=str(repo_acme))},
            vault_path="vault://clients/acme",
        )
    )
    registry.register_client(
        ClientRecord(
            client_id="client_fintech",
            client_name="Fintech Corp",
            projects={"core": ProjectRecord(project_id="core", repo_path=str(repo_fintech))},
            vault_path="vault://clients/fintech",
        )
    )

    vault = ScopedVaultClient()
    vault.set_project_secrets("client_acme", "web", {"API_KEY": "acme_secret"})
    vault.set_project_secrets("client_fintech", "core", {"API_KEY": "fintech_secret"})

    return registry, vault, str(repo_acme), str(repo_fintech)


def test_cross_client_boundary_blocks_unauthorized_client(isolated_clients_fixture):
    registry, _, _, _ = isolated_clients_fixture
    scope_acme = registry.get_client_scope("client_acme", "web")

    with pytest.raises(CrossClientAccessViolationError) as exc_info:
        registry.assert_scope_boundary(scope_acme, target_client_id="client_fintech")

    assert "CROSS_CLIENT_VIOLATION" in str(exc_info.value)


def test_cross_client_boundary_blocks_foreign_repo_access(isolated_clients_fixture):
    registry, _, _, repo_fintech = isolated_clients_fixture
    scope_acme = registry.get_client_scope("client_acme", "web")

    with pytest.raises(CrossClientAccessViolationError) as exc_info:
        registry.assert_scope_boundary(
            scope_acme,
            target_client_id="client_acme",
            target_path=f"{repo_fintech}/database.sqlite",
        )

    assert "CROSS_SCOPE_PATH_VIOLATION" in str(exc_info.value)

