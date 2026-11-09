# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Universal Autonomous OS Operator & Co-Pilot (Project Igris) powered by VLM spatial vision, AT-SPI accessibility, dual-mode execution (Live Co-Pilot on `:0` vs Ghost Virtual Lab on `:99`), and remote mobile companionship.
- **Active Focus Module:** **Workspace Foundation & Core Action Driver Architecture (`apps/core-engine`)**.
- **Current Active Task:** **Professional Workspace Restructuring & Multi-PC Living Memory Initialization**:
  - **Milestone Status:** In progress — Workspace expanded into a multi-app monorepo structure with `.agents/memory/` protocol, multi-module directories (`apps/core-engine`, `apps/companion-web`, `apps/desktop-overlay`), and comprehensive living memory files.
  - **Workspace Restructuring:**
    1. Upgraded project from a basic script directory into a scalable multi-app monorepo.
    2. Moved core Python runtime into `apps/core-engine/` with its own `pyproject.toml` and config.
    3. Created scaffold for `apps/companion-web/` (Mobile WebRTC PWA) and `apps/desktop-overlay/` (Transparent HUD).
    4. Established living memory protocol under `.agents/memory/` (`HANDOVER.md`, `DECISIONS.md`, `ARCHITECTURE.md`).
    5. Established root `AGENTS.md` directive enforcing multi-workstation continuity and universal Bengali documentation with English technical keywords.
  - **Immediate Next Steps:**
    1. Complete living memory documentation (`DECISIONS.md`, `ARCHITECTURE.md`).
    2. Create `Igris.code-workspace` configuration.
    3. Finalize `docs/` technical specifications.
    4. Kick off Phase 1 implementation in `apps/core-engine` (Xvfb virtual display manager and low-level mouse/keyboard driver).
  - **Files Modified This Session:**
    - `AGENTS.md` (Created root directive)
    - `.agents/memory/HANDOVER.md` (Created)
    - `.agents/memory/DECISIONS.md` (Pending)
    - `.agents/memory/ARCHITECTURE.md` (Pending)
    - `apps/core-engine/` (Relocated source code, pyproject, and config)
    - `apps/companion-mobile/README.md` (Created dedicated mobile app module scaffold)
    - `apps/companion-web/README.md` (Created)
    - `apps/desktop-overlay/README.md` (Created)
    - `README.md` (Pending update)

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Workspace Architecture, Multi-PC Memory, & Guardrails | **Active** | 100% complete workspace foundation |
| **Phase 1** | OS Action Drivers, Virtual Display (Xvfb), & Input Simulator | Upcoming | Robust headless & live input control |
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
