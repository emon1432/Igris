# Architecture Decision Records (`DECISIONS.md`)

> **Protocol Rule:** Before introducing new architectural patterns, external frameworks/libraries, or API schema changes, consult this record. When proposing significant architectural changes, record a new decision below.

---

## Decision Index

| ID | Title | Date | Status | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-001** | [Autonomous OS Operator Paradigm over Application-Specific APIs](#adr-001-autonomous-os-operator-paradigm-over-application-specific-apis) | 2026-11-10 | **Accepted** | Core Architecture / Brain |
| **ADR-002** | [Living Memory & Multi-PC Continuity Protocol](#adr-002-living-memory--multi-pc-continuity-protocol) | 2026-11-10 | **Accepted** | Entire Repository / `.agents` |
| **ADR-003** | [Dual-Mode Execution Model: Live Co-Pilot vs. Ghost Virtual Lab](#adr-003-dual-mode-execution-model-live-co-pilot-vs-ghost-virtual-lab) | 2026-11-10 | **Accepted** | OS Automation & Display |
| **ADR-004** | [Multi-App Monorepo Workspace Architecture](#adr-004-multi-app-monorepo-workspace-architecture) | 2026-11-10 | **Accepted** | Repository Layout |
| **ADR-005** | [Hybrid Perception Strategy: VLM Spatial Vision & Linux AT-SPI Tree](#adr-005-hybrid-perception-strategy-vlm-spatial-vision--linux-at-spi-tree) | 2026-11-10 | **Accepted** | Perception Layer |
| **ADR-006** | [Strict Language Separation: English Codebase, Bengali Dialogue](#adr-006-strict-language-separation-english-codebase-bengali-dialogue) | 2026-11-11 | **Accepted** | Communication & Codebase |

---

## ADR-001: Autonomous OS Operator Paradigm over Application-Specific APIs

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
Integrating discrete APIs for thousands of individual desktop applications (e.g., WhatsApp, Gmail, Zoom, Photoshop, VS Code) is unmaintainable and breaks when external APIs deprecate.

### Decision
Igris will not rely on application-specific APIs. Instead, it adopts the Universal Autonomous OS Operator paradigm:
1. Perceiving screen state via visual frames and UI trees.
2. Manipulating applications via mouse movements, clicks, drags, and keystrokes.
3. Leveraging background terminal/bash execution for headless developer and filesystem tasks.

### Consequences
- **Positive:** Works out-of-the-box on any installed software without requiring API credentials or developer endpoints.
- **Negative:** Visual latency must be managed via efficient frame grabbing (MSS) and deterministic element targeting (AT-SPI).

---

## ADR-002: Living Memory & Multi-PC Continuity Protocol

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
Context degradation occurs when working across multiple workstations or resuming new sessions.

### Decision
Establish an automated Living Memory Protocol under `.agents/memory/`:
1. Every session starts by reading `.agents/memory/HANDOVER.md`, `DECISIONS.md`, and `ARCHITECTURE.md`.
2. Every session wraps up by recording progress and next steps in `HANDOVER.md`.
3. Strict Git constraint: No automated `git commit` or `git add` without explicit user confirmation.

---

## ADR-003: Dual-Mode Execution Model: Live Co-Pilot vs. Ghost Virtual Lab

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
Direct input simulation on primary monitors interrupts active user workflows (movies, games, coding). Conversely, creative tasks require real-time visual collaboration on the user's screen.

### Decision
Implement a dual-mode execution engine:
1. **Live Co-Pilot Mode (`DISPLAY=:0`):** Works visibly on the primary screen. Backed by an emergency override that yields control when the physical mouse moves.
2. **Ghost Mode (`DISPLAY=:99` via Xvfb):** Executes silently on an invisible virtual display, keeping the primary display free of disruptions.

---

## ADR-004: Multi-App Monorepo Workspace Architecture

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
Igris encompasses multiple components: a Python daemon, a mobile companion app, and a desktop overlay HUD. Placing everything in a flat directory creates severe architectural entanglement.

### Decision
Structure the repository as a clean multi-app monorepo:
- `apps/core-engine/`: Python daemon, VLM planner, and OS drivers.
- `apps/companion-mobile/`: Native mobile client (Flutter / React Native).
- `apps/companion-web/`: Browser/PWA client.
- `apps/desktop-overlay/`: Live HUD overlay.
- `packages/`: Shared protocols and schemas.
- `docs/`: Technical research and specifications.

---

## ADR-005: Hybrid Perception Strategy: VLM Spatial Vision & Linux AT-SPI Tree

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
VLM-predicted coordinates can drift by a few pixels due to resolution scaling, risking missed clicks on small buttons.

### Decision
Adopt a hybrid perception stack:
1. **Macro Vision:** VLM understands window semantics and relative positioning.
2. **Micro Precision:** Linux AT-SPI accessibility bus queries exact bounding boxes `(x, y, w, h)` to lock onto the precise center of target components.

---

## ADR-006: Strict Language Separation: English Codebase, Bengali Dialogue

### Status
**Accepted** (2026-11-11)

### Context & Problem Statement
Mixing languages inside application files creates maintenance friction, syntax collisions, and poor developer experience.

### Decision
Enforce strict separation of languages:
1. **Conversational Communication:** All user-facing explanations and discussions are held in **Bengali**.
2. **Application Files & Codebase:** Strictly written in standard, professional **English** (all code, comments, docstrings, README files, ADRs, and specifications). No Bengali characters permitted in codebase files.
