"""Data Models for Client and Project Registry."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ProjectRecord(BaseModel):
    """Configuration record for an individual project or repository."""
    project_id: str
    repo_path: str
    default_branch: str = "main"
    allowed_domains: List[str] = Field(default_factory=list)
    test_command: str = "pytest"
    lint_command: Optional[str] = None


class ClientRecord(BaseModel):
    """Configuration record for an enterprise or individual client."""
    client_id: str
    client_name: str
    verified_senders: List[str] = Field(default_factory=list)
    projects: Dict[str, ProjectRecord] = Field(default_factory=dict)
    vault_path: str
    ai_restricted: bool = False

