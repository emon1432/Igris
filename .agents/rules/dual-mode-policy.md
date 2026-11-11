# Dual-Mode Routing Policy (Live vs. Ghost Mode)

Before executing any automated task, Igris must determine the target display environment based on these criteria:

## 1. Live Co-Pilot Mode Selection (`DISPLAY=:0`)
Selected when any of the following conditions are met:
1. The user explicitly requests live execution (e.g., *"Do this in front of me"*, *"Watch this"*, *"Take over the screen"*, *"Click here"*).
2. The task requires real-time interaction with an application already open on the primary screen (e.g., GIMP, Photoshop, active browser tab, code editor review).
3. The user wants visual collaboration.

## 2. Ghost Mode Selection (`DISPLAY=:99` via Xvfb)
Selected automatically when:
1. The user is actively engaged in a primary task (e.g., playing a movie, playing a game, writing code).
2. The task does not require visual supervision (e.g., background messaging, checking and organizing emails, downloading files, compiling code).
3. The command originates from the mobile companion app while the user is away.

## 3. Mode Switching Rules
* If requested to move a live task to the background, windows or processes should migrate to the virtual display.
* Ghost mode tasks announce completion via audio or notification without generating intrusive screen pop-ups on the primary display.
