# AGENTS.md - Root AI Agent Directive

> **Universal Workspace Guidance & Multi-PC Continuity Protocol**  
> Repository: `Igris` (Autonomous Linux OS Operator & Co-Pilot)  
> Last Updated: 2026-11-11

---

## 1. Repository Summary

**Igris** is a Linux-first Universal Autonomous OS Operator (Computer Use System). Operating without hardcoded third-party app APIs, it interacts with applications via Screen Vision, the Linux Accessibility Tree (AT-SPI), Virtual Display Isolation (Xvfb), and mouse/keyboard simulation—functioning like a human operator.

### Workspace Structure & Module Boundaries

| Directory / Module | Role & Responsibility | Tech Stack / Status |
| :--- | :--- | :--- |
| **`apps/core-engine/`** | Core background daemon, VLM reasoning brain, OS action drivers, audio capture, and local voice pipeline | **Python 3.10+**, AsyncIO, FastAPI, Pydantic, MSS, PyAutoGUI, Xvfb, AT-SPI, Faster-Whisper, Edge-TTS |
| **`apps/companion-mobile/`** | Dedicated mobile client (remote voice commanding, hands-free Bluetooth, remote PC monitoring) | Planned Mobile App (**Flutter** / **React Native**) with WebRTC & Push-to-Talk |
| **`apps/companion-web/`** | Lightweight web client (browser-based remote control & monitoring interface) | Planned PWA / Lightweight Web Client with WebSocket bridge |
| **`apps/desktop-overlay/`** | Live Co-Pilot mode screen overlay (laser pointer & bounding box visual feedback) | Planned PySide6 / Transparent Canvas Overlay (`DISPLAY=:0`) |
| **`packages/`** | Shared data types, RPC contracts, and protocol definitions | Modular shared schemas & utilities |
| **`docs/`** | Complete system architecture, roadmaps, technical specifications, and research | Markdown Documentation & Diagrams |
| **`.agents/memory/`** | Multi-PC living memory system (`HANDOVER.md`, `DECISIONS.md`, `ARCHITECTURE.md`) | Living state, ADRs, & continuous engineering continuity |
| **`.agents/rules/`** | Agent behavioral guardrails and safety policies | Markdown Guardrails |
| **`.agents/skills/`** | Executable OS automation and virtual display toolchains/runbooks | Procedural Toolchains & Runbooks |
| **`scripts/`** | System dependency installers and virtual display management scripts | Bash utilities (`setup_system_deps.sh`) |
| **`Igris.code-workspace`** | Multi-root IDE workspace configuration | VS Code / Antigravity IDE configuration |

---

## 2. Multi-PC Memory Protocol (MANDATORY)

To ensure seamless handovers and continuity across multiple workstations without losing context or requiring redundant explanations, **ALL AI AGENTS MUST ADHERE TO THIS PROTOCOL**:

```
+-----------------------------------------------------------------------------+
|                           AI AGENT SESSION LIFECYCLE                         |
|                                                                             |
|  1. SESSION KICKOFF                                                         |
|     Read: .agents/memory/HANDOVER.md                                        |
|     - Understand active sprint, recent progress, and immediate next steps.  |
|                                                                             |
|  2. ARCHITECTURAL GUARDRAILS                                                |
|     Read & Check: .agents/memory/DECISIONS.md & ARCHITECTURE.md             |
|     - Check ADRs before introducing dependencies, APIs, or architectural    |
|       modifications.                                                        |
|                                                                             |
|  3. EXECUTION                                                               |
|     - Follow module-specific guidelines.                                    |
|     - Keep changes minimal, tested, and aligned with conventions.           |
|                                                                             |
|  4. SESSION WRAP-UP                                                         |
|     Update: .agents/memory/HANDOVER.md                                      |
|     - Record completed work, active files, remaining blockers, and next     |
|       immediate tasks. DO NOT autonomously run git add or git commit.      |
+-----------------------------------------------------------------------------+
```

### Protocol Rules:

1. **Session Kickoff (Mandatory Step 1):**
   - At the beginning of any session, the agent **MUST read `.agents/memory/HANDOVER.md`**.
   - Review current active sprint, recent progress, and immediate next steps.
   - For architectural tasks, consult `.agents/memory/ARCHITECTURE.md` and `DECISIONS.md`.

2. **Architectural Guardrails (Pre-decision Step):**
   - Before introducing any new library, framework, or architectural modification, check `.agents/memory/DECISIONS.md` to avoid conflicts with prior architectural decision records.
   - When a major new decision is adopted, document it as an ADR (`ADR-00X`).

3. **Session Wrap-Up (Mandatory Final Step):**
   - Before ending a task or session, the agent **MUST update `.agents/memory/HANDOVER.md`**.
   - Document completed work, active/modified files, remaining blockers, and immediate next steps.
   - **STRICT GIT CONSTRAINT:** DO NOT run `git add` or `git commit` autonomously without explicit user instruction. Git staging and commits must be requested by the user.

4. **Universal Language Invariant (MANDATORY):**
   - **Chat / Conversational Interaction & Implementation Plans:** Always conducted in **Bengali**. All implementation plans, task roadmaps, and planning artifacts presented to the user must be written in Bengali (with technical identifiers, symbols, and file paths kept in backticks).
   - **Codebase & Application Files:** **STRICTLY ENGLISH ONLY**. All code, docstrings, inline comments, configuration files, specifications, documentation, and markdown files across the repository must be written in standard, professional English. No Bengali characters inside repo files.

5. **Mandatory Pre-Execution Approval Gate (MANDATORY):**
   - For any roadmap phase, major architectural milestone, or complex feature implementation, the agent **MUST NOT jump directly into coding or modifying files**.
   - The agent **MUST FIRST draft a structured implementation plan artifact** detailing the component architecture, file changes, security considerations, and test plan.
   - The agent must present the plan and explicitly wait for the user's review and approval. Implementation and code modifications may only commence after explicit user confirmation.

---

## 3. Adaptive Learning & Proactive Architecture Directive

The agent must act as a proactive senior software architect and engineering partner:

1. **Proactively Propose Optimal Alternatives:**
   - Present the most scalable, clean, and secure architectural paths before executing code.
2. **Autonomous Memory Maintenance:**
   - Keep `.agents/memory/DECISIONS.md` and `HANDOVER.md` synchronized as the project advances.
3. **Contextual Adaptation (Zero Micromanagement):**
   - Understand Linux system internals, virtual framebuffers, and multimodal perception to execute complete, end-to-end solutions independently.

---

## 4. Dual-Mode Execution & Safety Protocols

1. **Live Co-Pilot Mode (`DISPLAY=:0`):**
   - Operates directly on the user's active screen.
   - **Emergency Override:** If the user moves the physical mouse by more than 10 pixels or presses `Escape`, the agent immediately yields control.
2. **Ghost Mode (`DISPLAY=:99` via Xvfb):**
   - Operates on an isolated virtual display in the background.
   - Causes zero screen flickers, pop-ups, or mouse disruptions on the user's primary monitor.
3. **Destructive Action Confirmation:**
   - Permanent file deletion, destructive shell commands (`rm -rf`), or major branch pushes strictly require explicit user confirmation.
