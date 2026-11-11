# Safety & Display Isolation Specification

## 1. Scope & Objectives
For an autonomous computer-operating agent, safety and display isolation are foundational. Igris must guarantee that background tasks do not corrupt user data, disrupt active sessions, or execute unintended operations.

---

## 2. Virtual Display Isolation Protocols
1. **Process Sandboxing:** Background tasks run exclusively against the isolated Xvfb display socket.
2. **Clipboard Isolation:** The primary display and virtual display clipboards remain isolated by default to prevent leakage of credentials or sensitive user data.
3. **Resource Throttling:** Background applications are managed under process quotas to ensure zero performance degradation for foreground games or media playback.

---

## 3. Action Permission & Confirmation Matrix

| Operation Category | Autonomy Level | Enforcement Mechanism |
| :--- | :--- | :--- |
| Application Launching / Web Navigation | Autonomous | Allowed without prompts |
| File Inspection & Reading | Autonomous | Allowed without prompts |
| Code Modification / Local Editing | Semi-Autonomous | Allowed; user notified upon completion |
| Git Push / Deployment | Gated | Explicit verbal/text confirmation required |
| File Deletion (`rm`, trash purge) | Strict Gated | Hard prompt requiring positive confirmation |
| System Configuration (`sudo`, package removal) | Blocked | Prohibited unless explicitly issued by user |
