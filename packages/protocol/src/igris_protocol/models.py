"""Core Data Contracts and Schema Definitions.

Defines the fundamental data models shared across policy, ledger, orchestrator, and tools.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    """Hierarchical risk tiers governing tool invocation."""
    T0 = "T0"  # Read-only, zero side effects
    T1 = "T1"  # Local, isolated in branch/sandbox, fully reversible
    T2 = "T2"  # External impact, staging deployment, 3rd-party notes
    T3 = "T3"  # Irreversible, financial, client-facing, production data mutations


class TaskMode(str, Enum):
    """Operational mode governing active tool privileges."""
    CONVERSATIONAL = "CONVERSATIONAL"  # Pure conversation / screen Q&A (zero mutating tools)
    TRIAGE = "TRIAGE"                  # Inspecting external data (strictly read-only tools loaded)
    WORK = "WORK"                      # Project-scoped active engineering / execution


class ClientScope(BaseModel):
    """Defines strict organizational and repository boundaries."""
    client_id: str
    project_id: str
    repo_path: Optional[str] = None
    allowed_domains: List[str] = Field(default_factory=list)
    ai_restricted: bool = False
    vault_secret_path: Optional[str] = None


class ApprovalToken(BaseModel):
    """Cryptographic authorization token granting permission for T2/T3 execution."""
    token_id: str
    task_id: str
    action_type: str
    risk_tier: RiskTier
    payload_hash: str                  # SHA256 of the diff, email body, or payload
    granted_at: float
    granted_by: str                    # Strictly "SCREEN_BUTTON"; "VOICE" is invalid for T2/T3
    expires_at: float

    def is_expired(self, current_time: float) -> bool:
        return current_time > self.expires_at


class LedgerEntry(BaseModel):
    """Append-only cryptographic record of an action execution."""
    index: int
    prev_hash: str
    timestamp: float
    task_id: str
    tool_name: str
    risk_tier: RiskTier
    client_id: Optional[str] = None
    input_parameters: Dict[str, Any]
    approval_token_id: Optional[str] = None
    output_summary: str
    entry_hash: str

