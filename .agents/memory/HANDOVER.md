# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Supervised Personal AI Operations Assistant & Omni-Co-Pilot (Project Igris) for Khairul Islam Emon (@Khairul Islam Emon).
- **Current Milestone Status:** **PHASES 0 THROUGH 5 COMPLETED & 100% VERIFIED (139/139 Automated Tests Passing)**:
  - **Delivered Packages & Architectural Modules:**
    1. **`packages/protocol` (`igris_protocol`):** Brand definition (`brand.py`) and schemas (`models.py`: `RiskTier`, `TaskMode`, `ClientScope`, `ApprovalToken`, `LedgerEntry`).
    2. **`packages/policy_engine` (`igris_policy`):** Pure deterministic policy engine enforcing T0-T3 risk tiers, blocking write tools in `TRIAGE` mode (`P-02`), and enforcing screen button approvals (`P-01`, `M-01`).
    3. **`packages/ledger` (`igris_ledger`):** Append-only cryptographic action ledger with SHA-256 block chaining and `verify_chain_integrity()`.
    4. **`packages/kill_switch` (`igris_kill_switch`):** Universal emergency kill switch halting active tasks and revoking approval tokens (`K-01`).
    5. **`packages/cost_meter` (`igris_cost_meter`):** Budgeting and loop iteration limiter preventing infinite loops (`C-01`).
    6. **`packages/tool_sdk` (`igris_tool_sdk`):** Intercepting wrapper mediation layer enforcing kill switch check, cost meter step, policy check, sandboxed execution, ledger append, and secret redaction.
    7. **`packages/registry` (`igris_registry`):** `ClientRecord`, `ProjectRecord`, `ProjectRegistry`. Enforces single-project task binding and blocks cross-client access (`CrossClientAccessViolationError`).
    8. **`packages/vault_client` (`igris_vault`):** Scoped secret vault client with automatic redaction registration (`S-01`).
    9. **`tools/git_deploy` (`igris_git_tool`):** Sandboxed git operations (branching, diff generation, test runner) with T2/T3 gated staging push and production deploy.
    10. **`tools/mail` (`igris_mail`):** Email triage parser neutralizes zero-width unicode, fake XML delimiters, sender verification (`I-02`), financial record verification (`F-01`), and gated T3 outbound dispatch.
    11. **`IndependentTaskVerifier` (`igris.brain.verifier`):** Independent auditor evaluating proof packages (non-empty diff + clean test logs) before granting task completion (`V-01`).
    12. **`ApprovalManager` (`igris.remote.approval_manager`):** Manages staged approvals, issuing tokens strictly upon on-screen button confirmation (`M-01`). Rejects vocal approvals (`VoiceApprovalDisallowedError`).
    13. **`ConversationalMind` (`igris.brain.conversational_mind`):** Fast intent routing separating greetings/chit-chat ("Hello", "কেমন আছো") and screen perception Q&A from computer operating tasks—permanently eliminating accidental browser launches on normal speech.
    14. **Mobile Companion PWA (`apps/companion-web/`):** Full-featured responsive progressive web application (`index.html`, `css/style.css`, `js/app.js`) with on-screen button approval modal, live screen previews, live thought streaming, quick task capture ("বাসায় গিয়ে দেখব"), and one-tap emergency stop.
    15. **ShoppieFlyBD Analytics Tool (`tools/shoppiefly`):** Strictly read-only e-commerce reporting tool (`T0`) collecting revenue, order counts, top products, and abandoned carts.
    16. **Telegram Push & Interactive Approval Bridge (`packages/telegram_bridge`):** Real-time mobile alerts and interactive inline keyboard `[ ✅ Approve ]` / `[ ❌ Reject ]` bridge issuing verified `SCREEN_BUTTON` tokens (`M-01`).
    17. **Local PC Operator Tool (`tools/local_pc`):** Linux AT-SPI accessibility inspection (`T0`) and isolated Xvfb `:99` virtual display clicks/keystrokes (`T1`).
    18. **Local Voice Pipeline (`apps/core-engine/src/igris/voice/`):** Faster-Whisper local STT, Edge-TTS audio synthesis, and RMS VAD wake-word recognition ("Hey Igris").
    19. **Dual-Mode OS Drivers (`apps/core-engine/src/igris/action/`):** Live Co-Pilot on `:0` with hardware safety interlock and transient HUD laser pointer; Ghost Virtual Lab on `:99` via Xvfb.
  - **Automated Test Evidence:**
    - All 10 Core Evaluation Gates (`P-01`, `P-02`, `K-01`, `C-01`, `S-01`, `V-01`, `I-01`, `I-02`, `F-01`, `M-01`) verified and passing.
    - Full suite of package, tool, brain, perception, action, and gateway tests verified.
    - **Total Test Scorecard: 139 passed, 0 failed, 100% green in 10.47s.**
  - **Documentation & Reporting:**
    - Master specifications and architecture in `docs/PLAN.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`.
    - Phase completion reports: `docs/phases/phase-1.md` through `docs/phases/phase-5.md`.
    - Living memory synchronized in `HANDOVER.md` and `DECISIONS.md`.

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target / Gate |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Specifications, Architecture & Safety Eval Scaffolding | **Completed** | 81/81 tests passing; PLAN, SPEC, ARCHITECTURE approved |
| **Phase 1** | Policy Engine, Ledger, Kill Switch, Cost Meter & Mind | **Completed** | 103/103 tests passing; P-01, P-02, K-01, C-01 verified |
| **Phase 2** | Project Registry, Scoped Workspaces & Code Verification | **Completed** | 115/115 tests passing; S-01, V-01 & Client Isolation verified |
| **Phase 3** | Email Triage, Injection Defense & Verified Reply Drafts | **Completed** | 124/124 tests passing; I-01, I-02, F-01 & Red-Team verified |
| **Phase 4** | Push-to-Talk Voice, Mobile PWA & Approval Button UI (v1.0) | **Completed** | 128/128 tests passing; M-01 verified; v1.0 Accepted |
| **Phase 5** | ShoppieFlyBD Analytics, Telegram Bridge & Local PC Tool | **Completed** | 139/139 tests passing; Post-v1 Extensions verified |

---

## 3. Modified & Created Files in Phase 5

- `tools/shoppiefly/src/igris_shoppiefly/models.py` (Created)
- `tools/shoppiefly/src/igris_shoppiefly/client.py` (Created)
- `tools/shoppiefly/tests/test_shoppiefly_tool.py` (Created)
- `packages/telegram_bridge/src/igris_telegram/models.py` (Created)
- `packages/telegram_bridge/src/igris_telegram/bot.py` (Created)
- `packages/telegram_bridge/tests/test_telegram_bridge.py` (Created)
- `tools/local_pc/src/igris_local_pc/operator.py` (Created)
- `tools/local_pc/tests/test_local_pc_tool.py` (Created)
- `apps/core-engine/src/igris/perception/accessibility.py` (Updated with BoundingBox & query_elements)
- `apps/core-engine/src/igris/action/mouse_keyboard.py` (Updated with MouseKeyboardDriver alias)
- `docs/phases/phase-5.md` (Created Phase 5 Completion Report)
- `.agents/memory/HANDOVER.md` (Updated)
