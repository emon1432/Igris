# Multi-PC Session Handover (`Igris` Monorepo Root)

> **Protocol Rule:** Inspect this file at the start of every session across workstations. Update this file at the end of every session before committing.

---

## 1. Current Objective / Active Sprint

- **Monorepo High-Level Goal:** Build a Linux-first Universal Autonomous OS Operator & Co-Pilot (Project Igris) powered by VLM spatial vision, AT-SPI accessibility, dual-mode execution (Live Co-Pilot on `:0` vs Ghost Virtual Lab on `:99`), and remote mobile companionship.
- **Active Focus Module:** **Local Voice Pipeline & Audio Intelligence (`apps/core-engine/src/igris/voice`)**.
- **Current Active Task:** **Phase 4: Local Voice Pipeline & Audio Intelligence COMPLETED & VERIFIED**:
  - **Milestone Status:** 100% Completed & Verified with 41 automated test suites passing (all 14 voice tests passed).
  - **Completed Components:**
    1. **Audio Capture Layer (`capture.py`):** Real-time PCM microphone streamer via `sounddevice` / ALSA and PipeWire virtual loopback sink (`pw-record`) capturing desktop application audio (e.g. Google Meet, Zoom, YouTube) in 16kHz mono.
    2. **Wake-Word & VAD (`wake_word.py`):** Energy-based Voice Activity Detector (RMS thresholding and silence timeout) and phrase activator ("Hey Igris", "Igris") with casing preservation.
    3. **Speech-to-Text (`stt.py`):** Local `Faster-Whisper` engine running on CTranslate2 (`int8` quantization), providing sub-second transcription with word timestamps and confidence metrics without cloud dependencies.
    4. **Text-to-Speech (`tts.py`):** Natural speech synthesis using `Edge-TTS` with fully in-memory streaming directly to audio playback pipelines (zero `/tmp` file writes, 100% SonarQube compliant).
    5. **Meeting Intelligence Transcriber (`meeting_transcriber.py`):** Continuous audio buffer from PipeWire loopback sink producing rolling timestamped dialog lines and generating structured meeting summaries (executive summary, key discussion points, action items, and decisions).
    6. **Voice Co-Pilot Pipeline (`pipeline.py`):** Async state machine orchestrating hands-free execution: Wake-word detection -> Voice Command STT -> ReAct Loop Execution (`TaskOrchestrator`) -> Vocal status confirmation via TTS.
    7. **CLI Integration (`cli.py`):** Connected `--voice` flag for continuous hands-free co-pilot mode and `--record-meeting` flag for automated meeting note generation.
    8. **Automated Test Suite:** 41/41 unit and integration tests passing across actions, perception, brain, and voice packages.
  - **Immediate Next Steps (Phase 5):**
    1. Draft Implementation Plan for Phase 5: Remote Mobile Companion Gateway (WebRTC / Tailscale) & Desktop Overlay HUD (Transparent Canvas laser pointer).
    2. User to review and commit Phase 4 implementation.
  - **Files Modified This Session:**
    - `apps/core-engine/src/igris/voice/capture.py` (Created)
    - `apps/core-engine/src/igris/voice/wake_word.py` (Created)
    - `apps/core-engine/src/igris/voice/stt.py` (Created)
    - `apps/core-engine/src/igris/voice/tts.py` (Created)
    - `apps/core-engine/src/igris/voice/meeting_transcriber.py` (Created)
    - `apps/core-engine/src/igris/voice/pipeline.py` (Created)
    - `apps/core-engine/src/igris/voice/__init__.py` (Updated exports)
    - `apps/core-engine/src/igris/cli.py` (Added `--voice` and `--record-meeting` support)
    - `apps/core-engine/tests/voice/test_capture.py` (Created)
    - `apps/core-engine/tests/voice/test_wake_word.py` (Created)
    - `apps/core-engine/tests/voice/test_stt.py` (Created)
    - `apps/core-engine/tests/voice/test_tts.py` (Created)
    - `apps/core-engine/tests/voice/test_meeting_transcriber.py` (Created)
    - `apps/core-engine/tests/voice/test_voice_pipeline.py` (Created)
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
| **Phase 5** | Remote Mobile Companion Gateway (WebRTC / Tailscale) & Desktop HUD | **Up Next** | Anywhere mobile control & live laser overlay |

---

## 3. Environment & Prerequisites

- **OS:** Linux (Ubuntu/Debian environment).
- **Display Server:** X11 / Wayland with XWayland support.
- **Required System Packages:** `xvfb`, `xdotool`, `imagemagick`, `ffmpeg`, `at-spi2-core`, `gir1.2-atspi-2.0`.
- **Python Version:** Python 3.10+ in dedicated virtual environment (`venv`).
