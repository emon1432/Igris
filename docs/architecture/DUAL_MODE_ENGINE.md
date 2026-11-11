# Dual-Mode Execution Engine (Live vs. Ghost Mode)

## Overview
A defining capability of Igris is its **Dual-Mode Engine**, allowing the system to operate either visibly on the primary screen or silently inside an isolated background environment.

---

## 1. Live Co-Pilot Mode (Foreground / Astra Style)

### 1.1 Objectives & Use Cases
* Creative workflows (e.g., GIMP, Photoshop, Blender, Figma UI editing, browser inspection).
* Real-time collaborative pairing where the user explicitly requests visual assistance.

### 1.2 Execution Mechanics
* **Target Display:** `DISPLAY=:0`
* **Cursor Injection:** `pyautogui` / `xdotool` dispatching real hardware events.
* **Laser Overlay:** Before clicking, `apps/desktop-overlay` renders a brief semi-transparent highlight over the target coordinate.

### 1.3 Emergency Interlock
* Background listener continuously monitors hardware pointer coordinates.
* If the user moves the physical mouse or presses `Escape`:
  1. The active automation loop halts immediately.
  2. Input control returns to the user with zero resistance.
  3. Spoken notification confirms: *"Control returned to user."*

---

## 2. Ghost Mode (Background / Isolated Virtual Lab)

### 2.1 Objectives & Use Cases
* Background tasks (e.g., WhatsApp messaging, file organization, email digest generation, test execution).
* Operating while the user watches a movie, attends a meeting, or plays games.

### 2.2 Architectural Mechanics
* **Virtual Framebuffer:** Managed by `Xvfb` running on `DISPLAY=:99`.
* **Resolution:** 1920x1080 24-bit truecolor.
* **App Sandboxing:** Applications are launched under the virtual display socket:
  ```bash
  DISPLAY=:99 <command> &
  ```
* **Isolation:** Zero mouse displacement, window pop-ups, or audio interference on the primary screen.
