---
name: virtual-display
description: Guide and runbook to spawn, manage, and isolate GUI applications on an Xvfb virtual framebuffer display on Linux.
---

# Virtual Display Management Skill (Xvfb)

This skill provides step-by-step procedures for spawning, controlling, and terminating isolated virtual displays (`DISPLAY=:99`) on Linux, keeping the primary user display clean during automated tasks.

## 1. Starting the Virtual Display

```bash
# Launch Xvfb on display :99 at 1920x1080 24-bit resolution
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
```

## 2. Launching Applications Headlessly

Prefix applications with the virtual display environment variable:
```bash
DISPLAY=:99 google-chrome-stable --no-sandbox &
DISPLAY=:99 whatsapp-for-linux &
```

## 3. Capturing Virtual Frames

```bash
# Capture full screenshot of virtual display :99 using ImageMagick
import -window root -display :99 /tmp/virtual_frame.png
```

## 4. Injecting Input Events

```bash
# Send mouse movements and keystrokes to the virtual display
xdotool -display :99 mousemove 500 400 click 1
xdotool -display :99 type "Hello Naeem"
```

## 5. Teardown & Cleanup

```bash
# Terminate Xvfb process upon daemon shutdown
killall Xvfb
```
