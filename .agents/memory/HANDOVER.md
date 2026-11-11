# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Universal Autonomous OS Operator & Co-Pilot (Project Igris) powered by VLM spatial vision, AT-SPI accessibility, dual-mode execution (Live Co-Pilot on `:0` vs Ghost Virtual Lab on `:99`), and remote mobile companionship.
- **Active Focus Module:** **Workspace Foundation & Core Action Driver Architecture (`apps/core-engine`)**.
- **Current Active Task:** **Language Policy Realignment & Workspace English Standardization**:
  - **Milestone Status:** Completed — Enforced strict language separation per user directive: Conversational interactions remain in Bengali, while all repository files, code, docstrings, READMEs, specifications, and living memory records are standardized strictly in English.
  - **Completed Actions:**
    1. Updated `GEMINI.md` and `AGENTS.md` with the strict English-only invariant for codebase files.
    2. Translated and standardized `README.md`, `.agents/memory/*`, `.agents/rules/*`, `.agents/skills/*`, and `docs/*` into English.
    3. Confirmed workspace integrity across `apps/core-engine`, `apps/companion-mobile`, and `apps/desktop-overlay`.
  - **Immediate Next Steps:**
    1. Initialize Python virtual environment inside `apps/core-engine/`.
    2. Implement Phase 1: Virtual Display Manager (`apps/core-engine/src/igris/action/virtual_display.py`) wrapping Xvfb lifecycle.
    3. Implement Mouse/Keyboard low-level driver (`apps/core-engine/src/igris/action/mouse_keyboard.py`) supporting both `:0` and `:99`.
    4. Write integration test verifying headless GUI invocation and screenshot verification.
  - **Files Modified This Session:**
    - `GEMINI.md`
    - `AGENTS.md`
    - `README.md`
    - `apps/companion-mobile/README.md`
    - `apps/companion-web/README.md`
    - `apps/desktop-overlay/README.md`
    - `.agents/rules/safety-protocols.md`
    - `.agents/rules/dual-mode-policy.md`
    - `.agents/skills/virtual-display/SKILL.md`
    - `.agents/skills/screen-perception/SKILL.md`
    - `.agents/specs/ARCHITECTURE.md`
    - `.agents/memory/HANDOVER.md`
    - `.agents/memory/DECISIONS.md`
    - `.agents/memory/ARCHITECTURE.md`
    - `docs/architecture/DUAL_MODE_ENGINE.md`
    - `docs/roadmap/PHASED_EXECUTION_ROADMAP.md`
    - `docs/specs/SAFETY_AND_ISOLATION_SPEC.md`
    - `docs/research/LINUX_DESKTOP_AUTOMATION.md`

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Workspace Architecture, Multi-PC Memory, & Guardrails | **Completed** | 100% complete workspace foundation |
| **Phase 1** | OS Action Drivers, Virtual Display (Xvfb), & Input Simulator | **Up Next** | Robust headless & live input control |
| **Phase 2** | Screen Perception Engine (MSS + AT-SPI + VLM Spatial Mapping) | Upcoming | High-speed frame capture & element localization |
| **Phase 3** | Autonomous Reasoning Loop (ReAct: Observe $\rightarrow$ Act $\rightarrow$ Verify) | Upcoming | End-to-end task execution (WhatsApp, browser, files) |
| **Phase 4** | Local Voice Pipeline & Audio Loopback (Wake-word, STT, TTS, Meet) | Upcoming | Voice-driven interaction & meeting minutes |
| **Phase 5** | Remote Mobile Companion Gateway (WebRTC / Tailscale) & Desktop HUD | Upcoming | Anywhere mobile control & live laser overlay |

---

## 3. Environment & Prerequisites

- **OS:** Linux (Ubuntu/Debian environment).
- **Display Server:** X11 / Wayland with XWayland support.
- **Required System Packages:** `xvfb`, `xdotool`, `imagemagick`, `ffmpeg`, `at-spi2-core`, `gir1.2-atspi-2.0`.
- **Python Version:** Python 3.10+ in dedicated virtual environment (`venv`).
