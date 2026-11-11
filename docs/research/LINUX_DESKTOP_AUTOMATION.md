# Technical Research: Linux Desktop Automation & Perception

## 1. Input Injection Tooling Comparison

| Tool | Supported Environments | Strengths | Limitations | Role in Igris |
| :--- | :--- | :--- | :--- | :--- |
| **`xdotool`** | X11 / Xvfb | Highly reliable, fast, supports window targeting | Requires XWayland on Wayland | Primary driver for Xvfb and X11 |
| **`ydotool`** | Wayland & X11 | Operates at the `uinput` kernel level | Requires background `ydotoold` daemon | Secondary fallback driver on pure Wayland |
| **`PyAutoGUI`** | Cross-Platform | Native Python API, built-in coordinate tracking | Requires display environment variable switching | Live Co-Pilot helper |

---

## 2. Screen Perception Pipeline

* **MSS (Multiple Screen Shots):**
  - Utilizes `XGetImage` or X11 shared memory extension (XShm).
  - Captures full HD frames in approximately 10–15ms, minimizing perception latency.
* **AT-SPI (Assistive Technology Service Provider Interface):**
  - Communicates directly via D-Bus with GTK, Qt, and browser accessibility trees.
  - Returns exact pixel bounding boxes `(x, y, w, h)` for buttons, labels, and text fields, eliminating coordinate drift.
