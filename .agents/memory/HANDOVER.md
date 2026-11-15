# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Supervised Personal AI Operations Assistant & Omni-Co-Pilot (Project Igris) for Khairul Islam Emon (@Khairul Islam Emon).
- **Active Focus Phase:** **Phase 1 — Skeleton, Deterministic Policy Engine, Action Ledger, Kill Switch & Cost Meter**.
- **Current Milestone Status:** **Phase 1 COMPLETED & 100% VERIFIED (103/103 Automated Tests Passing)**:
  - **Delivered Packages & Architectural Modules:**
    1. **`packages/protocol` (`igris_protocol`):** Brand definition (`brand.py`) and core Pydantic data contracts (`RiskTier`, `TaskMode`, `ClientScope`, `ApprovalToken`, `LedgerEntry`).
    2. **`packages/policy_engine` (`igris_policy`):** Deterministic pure-code policy engine with zero LLM/IO imports. Enforces T0–T3 risk tiers, blocks write tools in `TRIAGE` mode, and strictly forbids voice approvals for T2/T3.
    3. **`packages/ledger` (`igris_ledger`):** Append-only cryptographic action ledger with SHA-256 block chaining and `verify_chain_integrity()`.
    4. **`packages/kill_switch` (`igris_kill_switch`):** Multi-tier emergency kill switch that halts active tasks, revokes active approval tokens, and raises `KillSwitchEngagedError` upon subsequent invocations.
    5. **`packages/cost_meter` (`igris_cost_meter`):** Budgeting and loop iteration limiter preventing runaway agent loops (`IterationLimitExceededError`, `BudgetExhaustedError`).
    6. **`packages/tool_sdk` (`igris_tool_sdk`):** Intercepting wrapper mediation layer enforcing kill switch check, cost meter step, policy check, sandboxed execution, ledger append, and secret redaction. Mock tools (`mock_read_email`, `mock_deploy_staging`, etc.) for Phase 1 verification.
    7. **`conversational_mind.py` (`igris.brain`):** Fast intent classifier and conversational respondent distinguishing greetings/chit-chat ("Hello", "কেমন আছো") and screen inspection questions from actionable OS operating tasks—permanently preventing unintended browser launches on normal speech.
  - **Automated Test Evidence:**
    - `evals/cases/test_p01_approval_gate.py`: PASSED (P-01 Gate verified against production `igris_policy`).
    - `evals/cases/test_p02_triage_readonly.py`: PASSED (P-02 Gate verified against production `igris_policy`).
    - `evals/cases/test_k01_kill_switch.py`: PASSED (K-01 Gate verified against production `igris_kill_switch`).
    - `evals/cases/test_c01_cost_meter.py`: PASSED (C-01 Gate verified against production `igris_cost_meter`).
    - All unit tests in `packages/*/tests/`: PASSED.
    - All 54 core-engine tests: PASSED.
    - **Total Test Scorecard: 103 passed, 0 failed, 100% green in 10.16s.**
  - **Documentation & Reporting:**
    - Documented Phase 1 report in `docs/phases/phase-1.md`.
    - Updated open questions in `docs/OPEN_QUESTIONS.md`.

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target / Gate |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Specifications, Architecture & Safety Eval Scaffolding | **Completed** | 81/81 tests passing; PLAN, SPEC, ARCHITECTURE approved |
| **Phase 1** | Policy Engine, Ledger, Kill Switch, Cost Meter & Mind | **Completed** | 103/103 tests passing; P-01, P-02, K-01, C-01 verified |
| **Phase 2** | Project Registry, Scoped Workspaces & Code Verification | **Pending Approval** | S-01, V-01 passing; client isolation verified |
| **Phase 3** | Email Triage, Injection Defense & Verified Reply Drafts | **Planned** | I-01, I-02, F-01 passing; red-team injection tests |
| **Phase 4** | Push-to-Talk Voice, Mobile PWA & Approval Button UI (v1.0) | **Planned** | M-01 passing; mobile end-to-end approval flow |
| **Phase 5** | ShoppieFlyBD Analytics, Telegram/WhatsApp & Desktop Ops | **Planned** | Phase 5 extension tools |

---

## 3. Modified & Created Files in This Session

- `apps/core-engine/venv/lib/python3.14/site-packages/igris_packages.pth` (Created)
- `packages/protocol/src/igris_protocol/brand.py` (Created)
- `packages/protocol/src/igris_protocol/models.py` (Created)
- `packages/protocol/src/igris_protocol/__init__.py` (Created)
- `packages/policy_engine/src/igris_policy/engine.py` (Created)
- `packages/policy_engine/src/igris_policy/__init__.py` (Created)
- `packages/policy_engine/tests/test_policy_engine.py` (Created)
- `packages/ledger/src/igris_ledger/ledger.py` (Created)
- `packages/ledger/src/igris_ledger/__init__.py` (Created)
- `packages/ledger/tests/test_ledger.py` (Created)
- `packages/kill_switch/src/igris_kill_switch/manager.py` (Created)
- `packages/kill_switch/src/igris_kill_switch/__init__.py` (Created)
- `packages/kill_switch/tests/test_kill_switch.py` (Created)
- `packages/cost_meter/src/igris_cost_meter/limiter.py` (Created)
- `packages/cost_meter/src/igris_cost_meter/__init__.py` (Created)
- `packages/cost_meter/tests/test_cost_meter.py` (Created)
- `packages/tool_sdk/src/igris_tool_sdk/wrapper.py` (Created)
- `packages/tool_sdk/src/igris_tool_sdk/mock_tools.py` (Created)
- `packages/tool_sdk/src/igris_tool_sdk/__init__.py` (Created)
- `packages/tool_sdk/tests/test_tool_sdk.py` (Created)
- `apps/core-engine/src/igris/brain/conversational_mind.py` (Created)
- `apps/core-engine/tests/brain/test_conversational_mind.py` (Created)
- `evals/cases/test_p01_approval_gate.py` (Updated to real package)
- `evals/cases/test_p02_triage_readonly.py` (Updated to real package)
- `evals/cases/test_k01_kill_switch.py` (Updated to real package)
- `evals/cases/test_c01_cost_meter.py` (Updated to real package)
- `docs/phases/phase-1.md` (Created)
- `docs/OPEN_QUESTIONS.md` (Updated)
- `.agents/memory/HANDOVER.md` (Updated)
