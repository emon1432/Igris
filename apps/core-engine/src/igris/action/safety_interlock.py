"""Safety Interlock and Physical Mouse Override Listener."""

import logging
import math
import threading
import time
from typing import Callable, List, Optional

logger = logging.getLogger("igris.action.safety_interlock")


class SafetyInterlockListener:
    """Monitors user inputs to trigger emergency stops when the human overrides control."""

    def __init__(
        self,
        mouse_threshold_px: int = 12,
        emergency_keys: Optional[List[str]] = None,
        on_override_callback: Optional[Callable[[], None]] = None,
    ):
        self.mouse_threshold_px = mouse_threshold_px
        self.emergency_keys = set(emergency_keys or ["Escape"])
        self.on_override_callback = on_override_callback

        self._is_active = False
        self._thread: Optional[threading.Thread] = None
        self._last_cursor_pos: Optional[tuple[int, int]] = None
        self._expected_cursor_pos: Optional[tuple[int, int]] = None
        self._override_triggered = False
        self._mouse_listener = None
        self._key_listener = None

    @property
    def is_triggered(self) -> bool:
        """Check if an emergency override has been triggered."""
        return self._override_triggered

    def reset(self) -> None:
        """Reset the override trigger state."""
        self._override_triggered = False

    def notify_agent_move(self, x: int, y: int) -> None:
        """Inform the interlock of an intentional agent movement so it is not treated as an override."""
        self._expected_cursor_pos = (x, y)
        self._last_cursor_pos = (x, y)

    def _trigger_override(self, reason: str) -> None:
        """Execute the emergency override protocol."""
        if not self._override_triggered:
            self._override_triggered = True
            logger.warning("SAFETY OVERRIDE TRIGGERED: %s. Yielding control to human.", reason)
            if self.on_override_callback:
                try:
                    self.on_override_callback()
                except Exception as exc:
                    logger.error("Error executing safety override callback: %s", exc)

    def _monitor_loop(self) -> None:
        """Background loop using pynput or system coordinates."""
        try:
            from pynput import mouse, keyboard
        except ImportError:
            logger.warning("pynput not available; physical mouse override listener disabled.")
            return

        def on_move(x: int, y: int):
            if not self._is_active:
                return

            if self._last_cursor_pos is None:
                self._last_cursor_pos = (x, y)
                return

            # Check if this movement diverges significantly from agent-expected position
            last_x, last_y = self._last_cursor_pos
            delta = math.hypot(x - last_x, y - last_y)

            if delta > self.mouse_threshold_px:
                # Verify if agent expected this movement
                if self._expected_cursor_pos:
                    exp_x, exp_y = self._expected_cursor_pos
                    dist_to_expected = math.hypot(x - exp_x, y - exp_y)
                    if dist_to_expected < self.mouse_threshold_px:
                        self._last_cursor_pos = (x, y)
                        return

                self._trigger_override(f"Physical mouse movement detected (delta: {delta:.1f}px)")

            self._last_cursor_pos = (x, y)

        def on_press(key):
            if not self._is_active:
                return
            try:
                key_name = key.name if hasattr(key, "name") else str(key)
                if key_name in self.emergency_keys:
                    self._trigger_override(f"Emergency key pressed ({key_name})")
            except Exception:
                pass

        try:
            self._mouse_listener = mouse.Listener(on_move=on_move)
            self._key_listener = keyboard.Listener(on_press=on_press)
            self._mouse_listener.start()
            self._key_listener.start()

            while self._is_active:
                time.sleep(0.05)
        except Exception as exc:
            logger.debug("pynput listener loop closed: %s", exc)
        finally:
            if self._mouse_listener:
                try:
                    self._mouse_listener.stop()
                except Exception:
                    pass
            if self._key_listener:
                try:
                    self._key_listener.stop()
                except Exception:
                    pass

    def start(self) -> None:
        """Start the background safety listener thread."""
        if self._is_active:
            return
        self._is_active = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="SafetyInterlockThread")
        self._thread.start()
        logger.info("SafetyInterlockListener started.")

    def stop(self) -> None:
        """Stop the background safety listener."""
        self._is_active = False
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
        if self._key_listener:
            try:
                self._key_listener.stop()
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None
        logger.info("SafetyInterlockListener stopped.")
