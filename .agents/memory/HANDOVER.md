# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Universal Autonomous OS Operator & Co-Pilot (Project Igris) powered by VLM spatial vision, AT-SPI accessibility, dual-mode execution (Live Co-Pilot on `:0` vs Ghost Virtual Lab on `:99`), and remote mobile companionship.
- **Active Focus Module:** **Core OS Drivers & Virtual Display Engine (`apps/core-engine`)**.
- **Current Active Task:** **Phase 1: Core OS Drivers & Virtual Display Engine COMPLETED & VERIFIED**:
  - **Milestone Status:** 100% Completed & Verified with 11 automated test suites passing.
  - **Completed Components:**
    1. **Virtual Display Lifecycle Manager (`virtual_display.py`):** Spawns, monitors, and cleans up Xvfb virtual framebuffers (`DISPLAY=:99` or dynamic free display allocation). Verified socket readiness and context manager scoping.
    2. **Multi-Display Input Driver (`mouse_keyboard.py`):** Unified mouse movements, multi-clicks, dragging, scrolling, text typing, and hotkeys using `xdotool` with explicit display scoping (`DISPLAY=:99` or `:0`).
    3. **Safety Interlock & Mouse Override (`safety_interlock.py`):** Background thread monitoring hardware mouse displacement and emergency hotkeys (`Escape`). Tested override trigger and callback dispatch.
    4. **Async Terminal Runner (`terminal.py`):** Asynchronous bash process runner with timeout handling, display passing, and security regex filters blocking dangerous destructive commands (`rm -rf /`, `mkfs`, raw block writes).
    5. **Automated Test Suite (`tests/action/`):** 11 tests verifying lifecycle, input injection, timeout handling, security blocks, and end-to-end headless screenshot capture.
  - **Immediate Next Steps (Phase 2):**
    1. Implement Screen Perception Engine (`apps/core-engine/src/igris/perception/screen.py`): Ultra-fast MSS frame grabbing and image pre-processing.
    2. Implement Linux AT-SPI Tree Inspector (`apps/core-engine/src/igris/perception/accessibility.py`): Extracting UI hierarchy and deterministic bounding boxes.
    3. Implement VLM Spatial Client (`apps/core-engine/src/igris/brain/vlm_client.py`): Gemini multimodal spatial coordinate prediction.
  - **Files Modified This Session:**
    - `GEMINI.md` (Updated language policy: Implementation plans and planning artifacts in Bengali)
    - `AGENTS.md` (Updated Universal Language Invariant for implementation plans)
    - `README.md` (Added hero branding banner & architecture badges)
    - `docs/assets/igris-banner.jpg` (Added high-resolution project artwork)
    - `apps/core-engine/src/igris/action/virtual_display.py` (Created)
    - `apps/core-engine/src/igris/action/mouse_keyboard.py` (Created)
    - `apps/core-engine/src/igris/action/safety_interlock.py` (Created)
    - `apps/core-engine/src/igris/action/terminal.py` (Created)
    - `apps/core-engine/src/igris/action/__init__.py` (Updated exports)
    - `apps/core-engine/tests/action/test_virtual_display.py` (Created)
    - `apps/core-engine/tests/action/test_mouse_keyboard.py` (Created)
    - `apps/core-engine/tests/action/test_safety_interlock.py` (Created)
    - `apps/core-engine/tests/action/test_terminal.py` (Created)
    - `apps/core-engine/tests/action/test_integration_ghost_mode.py` (Created)
    - `.agents/memory/HANDOVER.md` (Updated)

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Workspace Architecture, Multi-PC Memory, & Guardrails | **Completed** | 100% complete workspace foundation |
| **Phase 1** | OS Action Drivers, Virtual Display (Xvfb), & Input Simulator | **Completed** | 11/11 automated tests passed |
| **Phase 2** | Screen Perception Engine (MSS + AT-SPI + VLM Spatial Mapping) | **Up Next** | High-speed frame capture & element localization |
| **Phase 3** | Autonomous Reasoning Loop (ReAct: Observe $\rightarrow$ Act $\rightarrow$ Verify) | Upcoming | End-to-end task execution (WhatsApp, browser, files) |
| **Phase 4** | Local Voice Pipeline & Audio Loopback (Wake-word, STT, TTS, Meet) | Upcoming | Voice-driven interaction & meeting minutes |
| **Phase 5** | Remote Mobile Companion Gateway (WebRTC / Tailscale) & Desktop HUD | Upcoming | Anywhere mobile control & live laser overlay |

---

## 3. Environment & Prerequisites

- **OS:** Linux (Ubuntu/Debian environment).
- **Display Server:** X11 / Wayland with XWayland support.
- **Required System Packages:** `xvfb`, `xdotool`, `imagemagick`, `ffmpeg`, `at-spi2-core`, `gir1.2-atspi-2.0`.
- **Python Version:** Python 3.10+ in dedicated virtual environment (`venv`).
