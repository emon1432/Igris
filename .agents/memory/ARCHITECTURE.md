# System Architecture Specification (`.agents/memory/ARCHITECTURE.md`)

> **Protocol Rule:** This document serves as the master living architectural reference across workstations. Any major subsystem addition or architectural modification must be reflected here.

---

## 1. End-to-End System Topology

```mermaid
flowchart TD
    subgraph Clients ["1. Clients & Ingestion Channels"]
        MIC["Desktop Microphone (Wake-Word + STT)"]
        MOBILE["Mobile Companion (PWA / WebSockets)"]
        CLI["CLI Controller"]
    end

    subgraph GatewayBrain ["2. Gateway & Conversational Mind"]
        GATEWAY["API Gateway (FastAPI / WebSockets)"]
        INTENT["Intent Classifier & Conversational Brain"]
        KILL_SWITCH["Global Kill Switch Interceptor"]
    end

    subgraph Orchestration ["3. Task Workspace & Orchestrator"]
        ORCH["Central Task Orchestrator"]
        REGISTRY["Client & Project Scope Registry"]
        COST["Cost Meter & Iteration Budget Limiter"]
        VERIFIER["Independent Task Verifier"]
    end

    subgraph SecurityCore ["4. Deterministic Policy & Ledger"]
        POLICY["Deterministic Policy Engine (T0-T3 Pure Functions)"]
        LEDGER["Append-Only Cryptographic Action Ledger"]
        VAULT["Secret Vault Storage Client"]
    end

    subgraph ToolSDK ["5. Sandboxed Tool Layer"]
        TOOL_WRAPPER["Tool SDK Wrapper (Policy & Ledger Interceptor)"]
        TOOL_GIT["Git & Deploy Sandbox Tool"]
        TOOL_MAIL["Email Client (Triage / Verified Draft)"]
        TOOL_WEB["Playwright Browser Automation"]
        TOOL_SHOPPIE["ShoppieFlyBD Analytics API Client"]
    end

    subgraph OSDrivers ["6. OS Action Drivers & Display Engine"]
        DUAL_ROUTER["Dual-Mode Display Router"]
        LIVE_OS["Live Co-Pilot Driver (DISPLAY=:0 + Safety Interlock)"]
        GHOST_OS["Ghost Virtual Lab (DISPLAY=:99 via Xvfb)"]
        HUD["Desktop Laser Overlay (apps/desktop-overlay)"]
        TTS["Voice Synthesis (Edge-TTS Pipeline)"]
    end

    MIC --> GATEWAY
    MOBILE --> GATEWAY
    CLI --> GATEWAY

    GATEWAY --> KILL_SWITCH
    KILL_SWITCH --> INTENT

    INTENT -->|Conversational Q&A / Voice| GATEWAY
    INTENT -->|Computer Operating Task| ORCH

    ORCH <--> REGISTRY
    ORCH <--> COST
    ORCH --> TOOL_WRAPPER
    ORCH --> VERIFIER

    TOOL_WRAPPER --> POLICY
    POLICY -->|Permit| LEDGER
    POLICY -->|Reject| ORCH
    LEDGER --> VAULT

    TOOL_WRAPPER --> TOOL_GIT
    TOOL_WRAPPER --> TOOL_MAIL
    TOOL_WRAPPER --> TOOL_WEB
    TOOL_WRAPPER --> TOOL_SHOPPIE
    TOOL_WRAPPER --> DUAL_ROUTER

    DUAL_ROUTER -->|Live Mode :0| LIVE_OS
    DUAL_ROUTER -->|Ghost Mode :99| GHOST_OS
    LIVE_OS --> HUD
    ORCH --> TTS
    TTS --> MIC
    TTS --> MOBILE
```

---

## 2. Core Architectural Subsystems

### 2.1 Conversational Brain & Intent Routing
- **Dual Intent Pipeline:**
  - **Conversational Route:** Directly synthesizes dialogue or answers screen questions without triggering desktop tool manipulation or mouse clicks.
  - **Operational Route:** Passes actionable user instructions to the Task Orchestrator within an isolated `TaskContext`.

### 2.2 Supervised Policy Engine (T0 to T3)
- Pure deterministic Python functions enforcing non-negotiable boundaries:
  - **T0 (Read-Only):** Automatic execution; logged in ledger.
  - **T1 (Local/Reversible):** Automatic execution in isolated branch/sandbox; verified before finish.
  - **T2 (External Impact):** Blocked until signed `ApprovalToken` is issued via on-screen UI button click.
  - **T3 (Irreversible/Financial):** Blocked until signed `ApprovalToken` with attached proof artifacts and source verification is confirmed via on-screen UI button click.
  - **Speech Boundary:** Voice input ("yes", "approve") cannot grant T2/T3 approval tokens.

### 2.3 Immutable Action Ledger
- Hash-chained append-only record storing `(timestamp, task_id, tool_name, risk_tier, client_id, inputs, approval_token, output_summary, entry_hash)`.
- Database role restricted strictly to `INSERT` and `SELECT` operations.

### 2.4 Dual-Mode Execution Mechanics
- **Live Co-Pilot Mode (`DISPLAY=:0`):** Direct interaction on user's primary desktop with active mouse/Escape safety interlock and transient HUD laser crosshairs.
- **Ghost Virtual Lab Mode (`DISPLAY=:99`):** Fully isolated background execution on Xvfb display socket.
