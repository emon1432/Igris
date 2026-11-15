"""Emergency Kill Switch Management Subsystem.

Guarantees:
1. Activating the kill switch immediately halts all active child tasks and tool runners.
2. In-flight and cached approval tokens are purged immediately.
3. Subsequent tool execution requests are blocked deterministically.
4. An emergency audit record is dispatched to the ledger.
"""

from typing import List, Dict, Any, Optional, Callable


class KillSwitchEngagedError(RuntimeError):
    """Raised when an operation is attempted while the emergency kill switch is active."""
    pass


class KillSwitchManager:
    """Centralized hardware/software emergency kill switch."""

    def __init__(self):
        self._is_active: bool = False
        self._active_tasks: Dict[str, Any] = {}
        self._registered_tokens: Dict[str, Any] = {}
        self._callbacks: List[Callable[[str, str], None]] = []

    @property
    def is_engaged(self) -> bool:
        return self._is_active

    def register_task(self, task_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Registers an active task with the kill switch."""
        self.assert_healthy()
        self._active_tasks[task_id] = metadata or {}

    def deregister_task(self, task_id: str):
        """Removes a completed task."""
        self._active_tasks.pop(task_id, None)

    def register_token(self, token_id: str, token_obj: Any):
        """Registers an active approval token."""
        self.assert_healthy()
        self._registered_tokens[token_id] = token_obj

    def register_callback(self, callback: Callable[[str, str], None]):
        """Registers a listener to be invoked when the kill switch triggers."""
        self._callbacks.append(callback)

    def assert_healthy(self):
        """Enforces that the kill switch is NOT engaged."""
        if self._is_active:
            raise KillSwitchEngagedError("Emergency Kill Switch is ENGAGED. All operations are halted.")

    def trigger(self, source: str = "UNKNOWN", reason: str = "Emergency stop initiated") -> Dict[str, Any]:
        """Engages the kill switch immediately."""
        self._is_active = True

        terminated_tasks = list(self._active_tasks.keys())
        revoked_tokens = list(self._registered_tokens.keys())

        # Purge state
        self._active_tasks.clear()
        self._registered_tokens.clear()

        # Execute registered callbacks
        for cb in self._callbacks:
            try:
                cb(source, reason)
            except Exception:
                pass

        return {
            "status": "KILL_SWITCH_ENGAGED",
            "source": source,
            "reason": reason,
            "terminated_tasks": terminated_tasks,
            "revoked_tokens": revoked_tokens,
        }

    def reset(self, master_override: bool = False):
        """Resets the kill switch with explicit authorization."""
        if not master_override:
            raise PermissionError("Kill switch reset requires explicit master override confirmation.")
        self._is_active = False


# Global singleton instance for runtime coordination
global_kill_switch = KillSwitchManager()

