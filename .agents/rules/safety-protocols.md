# Safety & Permission Protocols

Igris has direct low-level access to mouse, keyboard, and terminal execution. To guarantee user safety and prevent system corruption, all automated operations must strictly enforce these protocols:

## 1. Destructive Action Restrictions
* **File Deletion or Overwrite:** Permanent deletions (`rm -rf`, file trashing) or bulk source code overwrites require explicit verbal or prompt confirmation from the user.
* **System Configuration:** Running commands requiring `sudo`, altering kernel parameters, or uninstalling system packages without explicit user instructions is strictly prohibited.
* **Sensitive Credentials:** Password fields, private keys (`.env`, `id_rsa`), and payment details must never be logged or transmitted to external models.

## 2. Emergency Override & Interruption
* **Physical Mouse Movement:** During Live Co-Pilot mode, if the user moves the physical mouse by more than 10 pixels, Igris immediately yields mouse control and pauses execution.
* **Hotkey Interruption:** Pressing `Escape` or `Ctrl+Shift+Q` halts the active autonomous action loop immediately.

## 3. Action Audit Logging
* Every click, drag, keystroke, and shell execution must be recorded in `logs/actions.jsonl` with timestamps and frame references for full auditability.
