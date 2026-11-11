# Igris System Architecture Specification

## 1. Project Overview
**Igris** is a Linux-first Universal Autonomous OS Operator (Computer Use System). Instead of depending on fragile, app-specific APIs, Igris uses multimodal Screen Vision, the Linux Accessibility Tree (AT-SPI), and low-level mouse/keyboard simulation to accomplish arbitrary desktop workflows.

---

## 2. Dual-Mode Execution Model

### 2.1 Live Co-Pilot Mode (Foreground / Astra Style)
* **Target Display:** Primary Display (`DISPLAY=:0` / currently active screen).
* **Objective:** Direct visual collaboration with the user (e.g., photo editing, code reviews, live UI tasks).
* **Key Features:**
  - Real-time mouse and keyboard manipulation visible to the user.
  - Visual laser overlay / bounding box indicator highlighting target elements.
  - **Manual Override:** Physical mouse movement ($> 10\text{px}$) or pressing `Escape` immediately releases control to the user.

### 2.2 Ghost Mode (Background / Isolated Virtual Lab)
* **Target Display:** Virtual Framebuffer (`DISPLAY=:99` via Xvfb).
* **Objective:** Autonomous task completion without interrupting foreground user activities.
* **Key Features:**
  - Full application execution inside an invisible virtual desktop.
  - Zero mouse displacement or window pop-ups on the primary monitor.
  - Spoken completion audio or push notification upon task resolution.

---

## 3. Architectural Layers

```
+-------------------------------------------------------------+
|                 1. Command Interfaces                       |
|   - Local Microphone (Wake-Word + STT)                      |
|   - Mobile Remote Gateway (WebSockets / WebRTC / Tailscale) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 2. Central Agent Brain                      |
|   - Multi-Tier LLM & Vision-Language Model (VLM)            |
|   - Task Planner & Reasoning Engine (ReAct Loop)            |
|   - Dual-Mode Router (Live vs. Ghost Selection)             |
|   - Long-Term & Episodic Memory                             |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              3. Perception Layer (Eyes & Ears)              |
|   - High-Speed Screen Capture (MSS / Pillow)                |
|   - Linux AT-SPI Accessibility Tree Inspector               |
|   - PulseAudio / PipeWire Virtual Audio Loopback            |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|               4. Action Layer (Execution Hands)             |
|   - Mouse & Keyboard Simulator (xdotool, ydotool, PyAutoGUI)|
|   - Virtual Display Manager (Xvfb Manager)                  |
|   - Headless Terminal / Asynchronous Bash Engine            |
+-------------------------------------------------------------+
```

---

## 4. Safety Guardrails
1. **Confirmation Gateways:** Explicit confirmation required before deleting files, modifying OS configurations, or pushing directly to Git remotes.
2. **Display Isolation:** Background tasks remain isolated on virtual framebuffers.
3. **Audit Trail:** Action history, timestamps, and execution screenshots recorded in `logs/actions.jsonl`.
