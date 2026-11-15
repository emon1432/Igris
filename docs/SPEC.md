# Igris System Specification (SPEC.md)

> **Document Version:** 1.0.0  
> **Classification:** Engineering System Specification  
> **Status:** Active Reference

---

## 1. Operating Modes & Behavioral Contracts

Igris transitions deterministically between three distinct operational modes based on user intent and input context:

```
                  ┌─────────────────────────────────────────┐
                  │           Inbound User Event            │
                  └─────────────────────────────────────────┘
                                       │
                      Intent Classification (Fast Route)
                                       │
             ┌─────────────────────────┼─────────────────────────┐
             ▼                         ▼                         ▼
   ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
   │ Conversational /  │     │   Triage Mode     │     │    Work Mode      │
   │  Screen Q&A Mode  │     │                   │     │                   │
   │  (Zero OS clicks) │     │ (Read-Only Tools) │     │ (Isolated Scope)  │
   └───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 1.1 Conversational & Screen Q&A Mode
- **Purpose:** Handling greetings ("hello", "hey igris"), general inquiries, brainstorming, and real-time screen inspection queries ("what is on my screen right now?").
- **Tool Sandbox:** Completely unloads desktop manipulation, file mutation, and external dispatch tools.
- **Output:** Natural conversational dialogue (in Bengali or English), TTS voice playback, or informative markdown responses.
- **Guarantee:** Never opens browsers or clicks desktop elements when the operator simply speaks or greets the assistant.

### 1.2 Triage Mode
- **Purpose:** Inspecting incoming communications (e.g., reading emails, scanning GitHub notifications, reviewing uncommitted local changes).
- **Tool Sandbox:** Loads **strictly read-only tools** (IMAP reader, git log, file finder). Write-capable tools (SMTP sender, git push, shell mutators) are strictly prohibited from loading into memory.
- **Data Treatment:** Incoming text from emails, web links, or external attachments is treated as **untrusted data**, never as executable instructions.
- **Drafts as Data:** The agent can synthesize reply drafts, but drafts remain static data models. They cannot be dispatched within Triage Mode.

### 1.3 Work Mode
- **Purpose:** Executing concrete modifications, bug fixes, refactoring, feature development, and staging previews for a specific project.
- **Single-Project Scoping:** A Work Mode session binds strictly to a single `client_id` and `project_id`. Cross-project data access or token sharing is rejected by the policy engine.
- **Isolation:** Operations run in a dedicated git branch or containerized sandbox.
- **Two-Phase Commit:**
  - *Phase A (Preparation):* Agent creates diffs, runs tests, captures screenshots, and produces a verifiable proof package.
  - *Phase B (Execution):* Upon explicit operator confirmation via an on-screen UI button, the changes are committed, pushed, or deployed.

---

## 2. Core Data Models & Schemas

### 2.1 Risk Tier Enumeration
```python
from enum import Enum

class RiskTier(str, Enum):
    T0 = "T0"  # Read-only, zero side-effects
    T1 = "T1"  # Local, isolated, fully reversible
    T2 = "T2"  # External impact, staging, non-client outbound
    T3 = "T3"  # Irreversible, financial, client-facing, data destruction
```

### 2.2 Task Context & Scope
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ClientScope(BaseModel):
    client_id: str
    project_id: str
    repo_path: Optional[str] = None
    allowed_domains: List[str] = Field(default_factory=list)
    vault_secret_path: str

class TaskContext(BaseModel):
    task_id: str
    mode: str  # "CONVERSATIONAL" | "TRIAGE" | "WORK"
    scope: Optional[ClientScope] = None
    cost_budget_usd: float = 1.00
    max_iterations: int = 25
    current_iteration: int = 0
```

### 2.3 Approval Token Contract
```python
class ApprovalToken(BaseModel):
    token_id: str
    task_id: str
    action_type: str
    risk_tier: RiskTier
    payload_hash: str          # SHA256 of the diff or outgoing message
    granted_at: float
    granted_by: str            # "SCREEN_BUTTON_CLICK" (Voice strictly disallowed)
    expires_at: float
```

### 2.4 Immutable Action Ledger Entry
```python
class LedgerEntry(BaseModel):
    index: int
    prev_hash: str             # Cryptographic hash chain link
    timestamp: float
    task_id: str
    tool_name: str
    risk_tier: RiskTier
    client_id: Optional[str]
    input_parameters: Dict[str, Any]
    approval_token_id: Optional[str]
    output_summary: str
    entry_hash: str            # SHA256(index + prev_hash + payload)
```

---

## 3. Tool Mediation Pipeline

All tools are encapsulated by the `ToolSDK` wrapper. The execution pipeline enforces deterministic verification on every call:

```
[ Orchestrator ]
       │
       ▼
[ ToolSDK.invoke(tool, params, context, approval_token) ]
       │
       ├──> 1. PolicyEngine.check_permission(...)
       │        ├── Check Mode (e.g., Triage forbids write tools)
       │        ├── Check Scope (parameters match ClientScope)
       │        └── Check Risk Tier & Approval Token validity
       │
       ├──> [ Tool Execution in Sandboxed Runner ]
       │
       ├──> 2. Ledger.append_entry(...)
       │        └── Cryptographically chain entry to append-only database
       │
       └──> 3. Return Sanitized Execution Result
```

---

## 4. Verifiable Proof-of-Completion Protocol

A task cannot transition to status `COMPLETED` unless accompanied by a verified `ProofArtifact`:

1. **Code Modification Tasks:**
   - Unified git diff (`git diff HEAD~1`).
   - Clean automated test execution output (`pytest` or `npm test` exit code 0).
   - Static analysis / linter clean run report.
2. **Web / UI Tasks:**
   - Before and after visual screenshot comparison artifacts.
   - HTTP response code validation.
3. **Email / Communication Tasks:**
   - Exact text draft and verified recipient address match against client registry.
4. **Independent Verifier Check:** The builder agent cannot verify its own output. A distinct verifier process audits the proof artifact against initial prompt requirements before completion is accepted.
