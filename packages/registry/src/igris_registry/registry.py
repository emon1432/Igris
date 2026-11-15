"""Client & Project Scope Registry with Cross-Client Boundary Enforcement.

Guarantees:
1. Manages registered clients and their isolated projects.
2. Formulates strictly scoped ClientScope instances for TaskContext.
3. Enforces that operations executing under client A cannot access data, repositories,
   or credentials of client B (raises CrossClientAccessViolationError).
"""

from pathlib import Path
from typing import Dict, Optional, List
from igris_protocol.models import ClientScope
from igris_registry.models import ClientRecord, ProjectRecord


class CrossClientAccessViolationError(PermissionError):
    """Raised when an operation attempts to breach client boundaries."""
    pass


class ProjectRegistry:
    """Central registry maintaining client and project scopes."""

    def __init__(self):
        self._clients: Dict[str, ClientRecord] = {}

    def register_client(self, client: ClientRecord):
        """Registers a client configuration."""
        self._clients[client.client_id] = client

    def get_client(self, client_id: str) -> Optional[ClientRecord]:
        """Retrieves a client record."""
        return self._clients.get(client_id)

    def get_project(self, client_id: str, project_id: str) -> Optional[ProjectRecord]:
        """Retrieves an individual project record."""
        client = self.get_client(client_id)
        if not client:
            return None
        return client.projects.get(project_id)

    def get_client_scope(self, client_id: str, project_id: str) -> ClientScope:
        """Formulates an immutable ClientScope for task initialization."""
        client = self.get_client(client_id)
        if not client:
            raise KeyError(f"Client '{client_id}' is not registered.")

        project = client.projects.get(project_id)
        if not project:
            raise KeyError(f"Project '{project_id}' not found under client '{client_id}'.")

        return ClientScope(
            client_id=client.client_id,
            project_id=project.project_id,
            repo_path=project.repo_path,
            allowed_domains=project.allowed_domains,
            ai_restricted=client.ai_restricted,
            vault_secret_path=f"{client.vault_path}/{project.project_id}",
        )

    def assert_scope_boundary(
        self,
        active_scope: ClientScope,
        target_client_id: str,
        target_path: Optional[str] = None,
    ):
        """Deterministically validates that an operation respects the active client scope boundary."""
        # 1. Client Identity Boundary Check
        if target_client_id != active_scope.client_id:
            raise CrossClientAccessViolationError(
                f"CROSS_CLIENT_VIOLATION: Active session belongs to '{active_scope.client_id}', "
                f"access denied to target client '{target_client_id}'."
            )

        # 2. Filesystem Boundary Check (if path is provided)
        if target_path and active_scope.repo_path:
            active_repo = Path(active_scope.repo_path).resolve()
            attempted_path = Path(target_path).resolve()
            try:
                attempted_path.relative_to(active_repo)
            except ValueError:
                raise CrossClientAccessViolationError(
                    f"CROSS_SCOPE_PATH_VIOLATION: Attempted access to '{attempted_path}' "
                    f"which is outside active repository '{active_repo}'."
                )

    def list_clients(self) -> List[str]:
        """Returns list of registered client IDs."""
        return list(self._clients.keys())

