# ADR-0007: Supervised Operations Paradigm & Deterministic Policy Engine (T0-T3)

## Status
Accepted (2026-11-15)

## Context & Problem Statement
Autonomous AI agents that execute external mutations (sending emails, modifying production code, performing financial transactions) without strict human-in-the-loop oversight present unacceptable catastrophic risks. Furthermore, relying on LLM system prompts for security guardrails is fundamentally flawed due to prompt injection vulnerabilities and non-deterministic behavior.

## Decision
1. **Supervised by Default:** The agent operates as an operator and preparer. Irreversible, external, or mutating actions require explicit approval.
2. **Deterministic Pure-Code Policy Engine:** All tool calls are mediated through standard code that validates the operational mode (`TRIAGE` vs `WORK`), client scope, and risk tier (T0 to T3). LLMs are strictly forbidden from participating in security policy decisions.
3. **Risk Tier Hierarchy:**
   - **T0 (Read-Only):** Autonomous execution; logged in ledger.
   - **T1 (Local/Reversible):** Autonomous execution in branch/sandbox; owner reviews artifacts.
   - **T2 (External Impact):** Screen button approval mandatory; diff/draft previewed.
   - **T3 (Irreversible/Financial):** Screen button approval mandatory; proof attached, source verified.
4. **Speech Boundary:** Voice input cannot grant T2/T3 approvals; on-screen UI button confirmation is strictly required.
5. **Immutable Action Ledger:** Every tool call is cryptographically chained and recorded in an append-only ledger (`INSERT` and `SELECT` only).
6. **Proof Before Completion:** No task completion is recognized without verifiable artifacts (passing automated tests, git diffs, screenshots).

## Consequences
- **Positive:** Robust immunity against prompt injection escaping the sandbox, complete auditability, and zero risk of accidental unapproved outbound communications.
- **Negative:** Requires disciplined UI approval flow and independent verifier architecture.
