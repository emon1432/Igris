"""Unit Tests for Project Registry and Cross-Client Isolation."""

import pytest
from igris_registry.models import ClientRecord, ProjectRecord
from igris_registry.registry import ProjectRegistry, CrossClientAccessViolationError


@pytest.fixture
def populated_registry(tmp_path):
    repo_acme = tmp_path / "acme_repo"
    repo_acme.mkdir()
    repo_fintech = tmp_path / "fintech_repo"
    repo_fintech.mkdir()

    reg = ProjectRegistry()
    reg.register_client(
        ClientRecord(
            client_id="acme",
            client_name="Acme Corp",
            verified_senders=["john@acme.com"],
            projects={
                "web": ProjectRecord(project_id="web", repo_path=str(repo_acme), allowed_domains=["acme.com"])
            },
            vault_path="vault://clients/acme",
        )
    )
    reg.register_client(
        ClientRecord(
            client_id="fintech",
            client_name="FinTech Ltd",
            verified_senders=["sec@fintech.io"],
            projects={
                "core": ProjectRecord(project_id="core", repo_path=str(repo_fintech), allowed_domains=["fintech.io"])
            },
            vault_path="vault://clients/fintech",
            ai_restricted=True,
        )
    )
    return reg, str(repo_acme), str(repo_fintech)


def test_registry_get_scope(populated_registry):
    reg, repo_acme, _ = populated_registry
    scope = reg.get_client_scope("acme", "web")
    assert scope.client_id == "acme"
    assert scope.project_id == "web"
    assert scope.repo_path == repo_acme
    assert scope.ai_restricted is False


def test_registry_cross_client_access_blocked(populated_registry):
    reg, repo_acme, repo_fintech = populated_registry
    scope_acme = reg.get_client_scope("acme", "web")

    # Accessing fintech while in acme scope must raise CrossClientAccessViolationError
    with pytest.raises(CrossClientAccessViolationError) as exc_info:
        reg.assert_scope_boundary(scope_acme, target_client_id="fintech")

    assert "CROSS_CLIENT_VIOLATION" in str(exc_info.value)


def test_registry_cross_scope_path_blocked(populated_registry):
    reg, repo_acme, repo_fintech = populated_registry
    scope_acme = reg.get_client_scope("acme", "web")

    # Accessing a path inside fintech repo while in acme scope must raise
    unauthorized_file = f"{repo_fintech}/secrets.env"
    with pytest.raises(CrossClientAccessViolationError) as exc_info:
        reg.assert_scope_boundary(scope_acme, target_client_id="acme", target_path=unauthorized_file)

    assert "CROSS_SCOPE_PATH_VIOLATION" in str(exc_info.value)

