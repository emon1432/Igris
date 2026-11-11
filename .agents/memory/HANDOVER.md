# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Universal Autonomous OS Operator & Co-Pilot (Project Igris) powered by VLM spatial vision, AT-SPI accessibility, dual-mode execution (Live Co-Pilot on `:0` vs Ghost Virtual Lab on `:99`), and remote mobile companionship.
- **Active Focus Module:** **Autonomous VLM Resilience & Live Operational Deployment (`apps/core-engine/src/igris/brain/vlm_client.py`, `.env`)**.
- **Current Active Task:** **Live Visible On-Screen Autonomous Browser Automation COMPLETED & VERIFIED**:
  - **Milestone Status:** 100% Completed & Demonstrated live on user's primary display (`DISPLAY=:0`) with visible on-screen browser and laser cursor interaction.
  - **Visible Live Automation Demonstration Execution:**
    - Ran live visible browser automation: `visible_browser_demo.py` on primary display (`:0`).
    - **Step 1:** Successfully spawned visible maximized Google Chrome browser on user's desktop.
    - **Step 2:** Navigated to YouTube directly.
    - **Step 3:** Injected and projected glowing neon laser cursor (`#FF0055`) with cyan ripple pulse.
    - **Step 4:** Glided cursor visibly across screen to YouTube search bar `(669, 28)`.
    - **Step 5:** Clicked search bar with visual ripple, then typed `"Plabon World"` character-by-character with realistic typing delay.
    - **Step 6:** Moved cursor to the search button `(962, 28)`, triggered click animation, and submitted search.
    - **Step 7:** Loaded YouTube video results, scrolled down through videos, and kept window open for visual verification before clean exit.
  - **Hardware Microphone Integration & Vocal Acknowledgment:**
    - Resolved PortAudio library missing warning (`libportaudio2`) by installing the system library.
    - Verified real-time hardware microphone capture (`MicrophoneCapture`) streaming 2048-byte real audio chunks via ALSA/PipeWire.
    - Pre-cached local Faster-Whisper STT model weights in `~/.cache/huggingface/hub/` for zero-latency speech recognition.
    - Configured customized vocal wake-word response: When the user says *"Hey Igris"*, Igris instantly speaks *"Yes, master, how can I help you?"* with a highlighted terminal banner.
    - Added phonetic variations (`"hey igris"`, `"hey egress"`, `"hey ingress"`, `"hey iris"`, etc.) for robust wake-phrase matching across different accents.
    - Automated test suite expanded to 54/54 tests passing cleanly.
  - **Runtime Stability & Model Cascade Enhancements:**
    1. **Gemini API Error Resolutions:** Configured `gemini-3.1-flash-lite` as the high-throughput, zero-quota-error primary model with automated fallback cascade across `["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]`.
    2. **Real-time Step Streaming:** Added `step_callback` to `TaskOrchestrator.execute_task()` and bridged it to `gateway.py` WebSocket broadcast so the web client displays live thoughts and actions in real time.
    3. **Automated Test Suite Expansion:** 53/53 tests passing cleanly in `pytest`.
  - **Completed Components:**
    1. **Remote Protocol Schemas (`protocol.py`):** Bidirectional RPC message contracts (`AuthRequest`, `TaskCommand`, `TaskUpdateMessage`, `TaskCompletedMessage`, `ScreenFrameMessage`, `EmergencyStopMessage`, `SystemStatusMessage`) with standard envelope serialization.
    2. **FastAPI & WebSocket Gateway Hub (`gateway.py`):** High-performance async gateway managing multi-client WebSockets (`/ws/companion`), live JPEG screen previews (`/api/screen/preview`), instant emergency abort (`/api/emergency/stop`), and background task execution bridging.
    3. **Desktop HUD Laser Overlay (`hud_overlay.py`):** Visual laser pointer indicator for Live Co-Pilot mode (`DISPLAY=:0`), projecting transient target crosshairs before clicks and keystrokes are executed.
    4. **Action Dispatcher Integration (`dispatcher.py`):** Automatically flashes the HUD laser overlay when dispatching actions on `:0` in Live mode.
    5. **Mobile Companion PWA Web Client (`apps/companion-web/`):** Full-featured responsive progressive web application (`index.html`, `css/style.css`, `js/app.js`) supporting Push-to-Talk voice recording, real-time screen canvas stream, live agent thoughts stream, mode switching, and one-tap emergency stop.
    6. **CLI Integration (`cli.py`):** Added `--gateway`, `--host`, and `--port` CLI options for launching the remote companion server.
    7. **Automated Test Suite:** 52/52 unit and integration tests passing across all packages (actions, perception, brain, voice, remote).
  - **Immediate Next Steps:**
    1. User review and git commit/push for Phase 5.
    2. Monorepo end-to-end integration and demonstration.
  - **Files Modified This Session:**
    - `apps/core-engine/src/igris/remote/protocol.py` (Created)
    - `apps/core-engine/src/igris/remote/gateway.py` (Created)
    - `apps/core-engine/src/igris/action/hud_overlay.py` (Created)
    - `apps/companion-web/index.html` (Created)
    - `apps/companion-web/css/style.css` (Created)
    - `apps/companion-web/js/app.js` (Created)
    - `apps/core-engine/src/igris/brain/dispatcher.py` (Integrated HUD overlay)
    - `apps/core-engine/src/igris/remote/__init__.py` (Updated exports)
    - `apps/core-engine/src/igris/cli.py` (Added `--gateway` support)
    - `apps/core-engine/tests/remote/test_protocol.py` (Created)
    - `apps/core-engine/tests/remote/test_gateway.py` (Created)
    - `apps/core-engine/tests/action/test_hud_overlay.py` (Created)
    - `.agents/memory/HANDOVER.md` (Updated)

---

## 2. Sprint Roadmap Overview

| Phase | Focus Area | Status | Target |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Workspace Architecture, Multi-PC Memory, & Guardrails | **Completed** | 100% complete workspace foundation |
| **Phase 1** | OS Action Drivers, Virtual Display (Xvfb), & Input Simulator | **Completed** | 11/11 automated tests passed |
| **Phase 2** | Screen Perception Engine (MSS + AT-SPI + VLM Spatial Mapping) | **Completed** | 22/22 automated tests passed (MSS + AT-SPI + VLM) |
| **Phase 3** | Autonomous Reasoning Loop (ReAct: Observe $\rightarrow$ Act $\rightarrow$ Verify) | **Completed** | 27/27 automated tests passed (Full ReAct loop) |
| **Phase 4** | Local Voice Pipeline & Audio Loopback (Wake-word, STT, TTS, Meet) | **Completed** | 41/41 automated tests passed (Voice + Meeting) |
| **Phase 5** | Remote Mobile Companion Gateway (WebRTC / Tailscale) & Desktop HUD | **Completed** | 52/52 automated tests passed (Gateway + HUD) |

---

## 3. Environment & Prerequisites

- **OS:** Linux (Ubuntu/Debian environment).
- **Display Server:** X11 / Wayland with XWayland support.
- **Required System Packages:** `xvfb`, `xdotool`, `imagemagick`, `ffmpeg`, `at-spi2-core`, `gir1.2-atspi-2.0`.
- **Python Version:** Python 3.10+ in dedicated virtual environment (`venv`).
