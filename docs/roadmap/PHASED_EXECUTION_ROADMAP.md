# Phased Execution Roadmap

Project Igris follows a 5-phase engineering roadmap designed for modularity, safety, and rapid validation:

---

## Phase 0: Workspace Foundation & Continuity Protocol (Completed)
* [x] Multi-App Monorepo architecture established (`apps/core-engine`, `apps/companion-mobile`, `apps/companion-web`, `apps/desktop-overlay`).
* [x] `.agents/memory/` living memory system operational (`HANDOVER.md`, `DECISIONS.md`, `ARCHITECTURE.md`).
* [x] Root `AGENTS.md` directive & strict English codebase rule established.
* [x] Multi-root `Igris.code-workspace` and system dependency scripts configured.

---

## Phase 1: Core OS Drivers & Virtual Display Engine (`apps/core-engine`)
* [ ] Implement `Xvfb` virtual framebuffer lifecycle manager.
* [ ] Implement low-level mouse and keyboard input driver (`xdotool`, `ydotool`, `pyautogui`).
* [ ] Implement safety interlock listener for immediate mouse override.
* [ ] Dual-mode execution smoke tests.

---

## Phase 2: Screen Perception & Spatial Mapping Engine
* [ ] High-speed frame grabber using `mss` supporting displays `:0` and `:99`.
* [ ] Linux `AT-SPI` accessibility tree traversal for deterministic UI targeting.
* [ ] Multimodal VLM integration (Gemini Flash/Pro spatial coordinate prediction).
* [ ] Coordinate scaling and hybrid bounding box resolver.

---

## Phase 3: Autonomous Reasoning Loop (ReAct Computer-Use Engine)
* [ ] End-to-end Observe $\rightarrow$ Reason $\rightarrow$ Act $\rightarrow$ Verify action loop.
* [ ] Multi-step desktop automation (browser launching, form filling, document searching).
* [ ] Headless terminal fast-path engine for filesystem, code editing, and Git commands.
* [ ] Destructive action confirmation gateways.

---

## Phase 4: Local Voice Pipeline & Audio Intelligence
* [ ] Wake-word detector ("Hey Igris").
* [ ] Sub-second low-latency STT (Faster-Whisper / Groq Whisper).
* [ ] Natural TTS synthesis (Edge-TTS / Piper TTS).
* [ ] PipeWire / PulseAudio virtual audio sink for meeting capture and minutes generation.

---

## Phase 5: Mobile Remote Companion & Desktop HUD
* [ ] Secure tunnel configuration (Tailscale / WireGuard / WebRTC).
* [ ] `apps/companion-mobile` native mobile client implementation.
* [ ] `apps/desktop-overlay` transparent HUD and laser target projection.
