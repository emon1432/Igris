# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Supervised Personal AI Operations Assistant & Omni-Co-Pilot (Project Igris) for Khairul Islam Emon (@Khairul Islam Emon).
- **Active Focus Phase:** **Phase 0 — Foundation, Specifications, Architecture & Safety Evaluation Suite Scaffolding**.
- **Current Milestone Status:** **Phase 0 COMPLETED & VERIFIED (81/81 Automated Tests Passing)**:
  - **Core Directives & Plan:**
    - Created `CLAUDE.md` at repository root defining the 8 unalterable directives, T0–T3 risk hierarchy, and architectural invariants.
    - Authored comprehensive `docs/PLAN.md` adapting the 18-page specification: Vision, Scope (v1 = Phases 0–4, Phase 5 = Extensions), Threat Model, Inviolable Design Principles, Risk Hierarchy, and Evals.
    - Authored `docs/SPEC.md` detailing operational modes (Conversational/Screen Q&A vs Triage Mode vs Work Mode), data models, tool mediation contracts, and proof-of-completion standards.
    - Authored `docs/ARCHITECTURE.md` and updated `.agents/memory/ARCHITECTURE.md` detailing the end-to-end multi-layer pipeline: Conversational Brain $\rightarrow$ Scoped Orchestrator $\rightarrow$ Pure-Code Policy Engine $\rightarrow$ Action Ledger $\rightarrow$ Tool SDK $\rightarrow$ OS Drivers.
    - Authored `docs/SECURITY.md` detailing the threat model (prompt injection, credential theft, client impersonation, financial claims, voice mishearing, approval fatigue).
    - Authored `docs/OPEN_QUESTIONS.md` cataloging 7 architectural decisions requiring operator review prior to Phase 1.
    - Updated `.agents/memory/DECISIONS.md` with **ADR-007: Supervised Operations Paradigm & Deterministic Policy Engine (T0-T3)**.
  - **Evaluation Test Suite Scaffolding (`evals/`):**
    - Built evaluation test cases covering all 10 core safety invariants:
      - `evals/cases/test_p01_approval_gate.py`: P-01 (T2/T3 blocked without screen button approval).
      - `evals/cases/test_p02_triage_readonly.py`: P-02 (Triage mode loads only read-only tools).
      - `evals/cases/test_k01_kill_switch.py`: K-01 (Emergency kill switch terminates tasks and revokes tokens).
      - `evals/cases/test_c01_cost_meter.py`: C-01 (Loop stops upon budget or iteration exhaustion).
      - `evals/cases/test_s01_vault_isolation.py`: S-01 (Secrets redacted from prompts, logs, and ledger).
      - `evals/cases/test_v01_proof_of_completion.py`: V-01 (No task completed without diff/test/screenshot proof).
      - `evals/cases/test_i01_injection_containment.py`: I-01 (Prompt injection cannot trigger mutating tools).
      - `evals/cases/test_i02_client_spoofing.py`: I-02 (Forged client senders trigger immediate security alert).
      - `evals/cases/test_f01_financial_verification.py`: F-01 (Financial claims require system-of-record validation).
      - `evals/cases/test_m01_voice_approval_boundary.py`: M-01 (Voice cannot authorize T2/T3 actions; screen button strictly required).
    - Added test fixtures in `evals/fixtures/` (`mails/sample_inbox.json`, `injection/payloads.json`, `clients/mock_registry.json`).
    - Added test harness in `evals/runner/eval_runner.py`.
    - Automated test verification: **81/81 tests passing** (54 engine tests + 27 eval assertions).

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target / Gate |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Specifications, Architecture & Safety Eval Scaffolding | **Completed** | 81/81 tests passing; PLAN, SPEC, ARCHITECTURE, SECURITY approved |
| **Phase 1** | Deterministic Policy Engine, Ledger, Kill Switch & Cost Meter | **Pending Approval** | P-01, P-02, K-01, C-01 passing on concrete implementations |
| **Phase 2** | Project Registry, Scoped Workspaces & Code Verification | **Planned** | S-01, V-01 passing; client isolation verified |
| **Phase 3** | Email Triage, Injection Defense & Verified Reply Drafts | **Planned** | I-01, I-02, F-01 passing; red-team injection tests |
| **Phase 4** | Push-to-Talk Voice, Mobile PWA & Approval Button UI (v1.0) | **Planned** | M-01 passing; mobile end-to-end approval flow |
| **Phase 5** | ShoppieFlyBD Analytics, Telegram/WhatsApp & Desktop Ops | **Planned** | Phase 5 extension tools |

---

## 3. Pending Operator Decisions Before Phase 1 (from `docs/OPEN_QUESTIONS.md`)

1. **Host Server Location (Q-01):** Dedicated self-hosted Linux VPS vs Cloud server? *(Recommended: Self-hosted Linux VPS)*.
2. **Backend Language Stack (Q-02):** Maintain Python 3.10+ across Gateway, Orchestrator, Policy Engine, and Tool SDK (leveraging our working engine)? *(Recommended: Python for backend + JS/TS for web PWA)*.
3. **Outbound Push Channel (Q-05):** Telegram Bot API vs Official WhatsApp Business Cloud API for real-time mobile push notifications and approval buttons? *(Recommended: Telegram Bot for instant interactive approval buttons; WhatsApp for official templates or draft-only)*.
4. **Client AI Restrictions (Q-06):** Are there specific client repositories that cannot touch external LLM APIs? *(Default: Configure in registry as `ai_restricted: true`)*.

---

## 4. Modified & Created Files in This Session

- `CLAUDE.md` (Created)
- `docs/PLAN.md` (Created)
- `docs/SPEC.md` (Created)
- `docs/ARCHITECTURE.md` (Created)
- `docs/SECURITY.md` (Created)
- `docs/OPEN_QUESTIONS.md` (Created)
- `docs/decisions/ADR-0007-supervised-operations-policy-engine.md` (Created)
- `.agents/memory/DECISIONS.md` (Updated)
- `.agents/memory/ARCHITECTURE.md` (Updated)
- `evals/fixtures/mails/sample_inbox.json` (Created)
- `evals/fixtures/injection/payloads.json` (Created)
- `evals/fixtures/clients/mock_registry.json` (Created)
- `evals/cases/test_p01_approval_gate.py` (Created)
- `evals/cases/test_p02_triage_readonly.py` (Created)
- `evals/cases/test_k01_kill_switch.py` (Created)
- `evals/cases/test_c01_cost_meter.py` (Created)
- `evals/cases/test_s01_vault_isolation.py` (Created)
- `evals/cases/test_v01_proof_of_completion.py` (Created)
- `evals/cases/test_i01_injection_containment.py` (Created)
- `evals/cases/test_i02_client_spoofing.py` (Created)
- `evals/cases/test_f01_financial_verification.py` (Created)
- `evals/cases/test_m01_voice_approval_boundary.py` (Created)
- `evals/runner/eval_runner.py` (Created)
- `.agents/memory/HANDOVER.md` (Updated)
