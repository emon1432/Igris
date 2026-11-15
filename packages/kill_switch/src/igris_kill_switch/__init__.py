"""Kill Switch package exports."""

from igris_kill_switch.manager import (
    KillSwitchManager,
    KillSwitchEngagedError,
    global_kill_switch,
)

__all__ = [
    "KillSwitchManager",
    "KillSwitchEngagedError",
    "global_kill_switch",
]

