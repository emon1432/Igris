# Igris Architecture Specification (ARCHITECTURE.md)

> **Document Version:** 2.0.0  
> **System Scope:** Supervised Multi-Modal Autonomous OS Operator & Operations Assistant  
> **Classification:** Living Architecture Specification

---

## 1. Multi-Tier End-to-End System Topology

```mermaid
flowchart TD
    subgraph Clients ["1. Client & Ingestion Interfaces"]
        WEB["Mobile & Desktop PWA (apps/companion-web)"]
        VOICE["Local Voice Pipeline (Push-to-Talk / Wake-Word)"]
        CLI["CLI Administrative Terminal"]
    end

    subgraph GatewayLayer ["2. Gateway & Conversational Brain"]
        GATEWAY["API Gateway (FastAPI / WebSockets)"]
        INTENT["Conversational Brain & Intent Router"]
        KILL["Global Kill Switch Interceptor"]
    end

    subgraph OrchestrationLayer ["3. Task Workspace & Orchestrator"]
        ORCH["Task Orchestrator"]
        REGISTRY["Client & Project Scope Registry"]
        COST["Cost Meter & Iteration Limiter"]
        VERIFIER["Independent Task Verifier"]
    end

    subgraph SecurityLayer ["4. Deterministic Policy & Ledger"]
        POLICY["Deterministic Policy Engine (T0-T3 Rules)"]
        LEDGER["Append-Only Cryptographic Action Ledger"]
        VAULT["Vault Secret Storage Client"]
    end

    subgraph ToolSDKLayer ["5. Mediated Tool SDK & Runners"]
        TOOL_SDK["Tool SDK Wrapper"]
        TOOL_GIT["Git & Deploy Sandbox Tool"]
        TOOL_MAIL["Email Client (Triage / Verified Draft)"]
        TOOL_WEB["Playwright Browser Automation"]
        TOOL_SHOPPIE["ShoppieFlyBD Analytics API Client"]
    end

    subgraph OSDriverLayer ["6. OS Action Drivers & Display Engine"]
        DUAL_ROUTER["Dual-Mode Display Router"]
        LIVE_OS["Live Co-Pilot Driver (DISPLAY=:0 + Safety Interlock)"]
        GHOST_OS["Ghost Virtual Lab (DISPLAY=:99 via Xvfb)"]
        HUD["Laser Pointer HUD Overlay"]
    end

    WEB <--> GATEWAY
    VOICE <--> GATEWAY
    CLI <--> GATEWAY

    GATEWAY --> KILL
    KILL --> INTENT

    INTENT -->|Direct Chat / Screen Q&A| GATEWAY
    INTENT -->|Operational Task| ORCH

    ORCH <--> REGISTRY
    ORCH <--> COST
    ORCH --> TOOL_SDK
    ORCH --> VERIFIER

    TOOL_SDK --> POLICY
    POLICY -->|Authorize| LEDGER
    POLICY -->|Deny| ORCH
    LEDGER --> VAULT

    TOOL_SDK --> TOOL_GIT
    TOOL_SDK --> TOOL_MAIL
    TOOL_SDK --> TOOL_WEB
    TOOL_SDK --> TOOL_SHOPPIE
    TOOL_SDK --> DUAL_ROUTER

    DUAL_ROUTER -->|Live Mode :0| LIVE_OS
    DUAL_ROUTER -->|Ghost Mode :99| GHOST_OS
    LIVE_OS --> HUD
```

---

## 2. Subsystem Boundaries and Responsibilities

### 2.1 Gateway & Conversational Intent Router
- **Role:** Central communications hub hosting authenticated WebSockets and REST endpoints.
- **Intent Classifier:** Distinguishes between:
  1. *Conversational Inquiries & Greetings:* Handled directly by LLM chat synthesis and Edge-TTS voice playback without launching desktop applications.
  2. *Screen Perception Q&A:* Inspects active display frame via MSS and AT-SPI to describe screen elements without executing mutating actions.
  3. *Computer Operating Tasks:* Routes to the Task Orchestrator with an initialized `TaskContext`.

### 2.2 Task Orchestration & Workspace Scoping
- **Role:** Manages the lifecycle of actionable tasks.
- **Scoping Invariant:** Binds each task to a specific `ClientScope` defined in `packages/registry`. Cross-project data leakage is structurally impossible.
- **Mode Enforcer:**
  - `TRIAGE`: Restricts active tools to read-only interfaces.
  - `WORK`: Launches isolated work branches/containers and coordinates the Independent Verifier.

### 2.3 Deterministic Policy Engine & Immutable Ledger
- **Role:** The non-negotiable security core of Igris.
- **Architecture:** Implemented as pure functions without external I/O or LLM reasoning.
- **Enforcement:**
  - Blocks any T2 or T3 action if not accompanied by an unexpired, cryptographically signed `ApprovalToken`.
  - Appends an immutable, hash-chained record of all invocations to the SQL `action_ledger` table.

### 2.4 Mediated Tool SDK & Runners
- **Role:** Sandboxed execution interfaces for filesystem, git, email, browser, and third-party APIs.
- **Rule:** No tool can be invoked directly by the agent; all calls route through `tool_sdk.invoke()`, guaranteeing policy inspection and ledger logging before and after every execution.

### 2.5 Dual-Mode OS Drivers
- **Live Co-Pilot Mode (`DISPLAY=:0`):** Operates on the primary screen alongside the user with hardware mouse/escape safety interlocks and HUD laser visualization.
- **Ghost Virtual Lab Mode (`DISPLAY=:99`):** Executes complex, headless, or background multi-step workflows on an Xvfb virtual framebuffer with zero desktop interruption.
