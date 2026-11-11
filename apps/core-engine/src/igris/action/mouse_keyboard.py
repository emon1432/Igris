"""Multi-display Mouse and Keyboard Input Driver using xdotool and PyAutoGUI."""

import logging
import os
import subprocess
from typing import Optional, Sequence

logger = logging.getLogger("igris.action.mouse_keyboard")


class InputDriverError(Exception):
    """Raised when mouse or keyboard simulation encounters an error."""
    pass


class InputDriver:
    """Dispatches mouse and keyboard events to primary (:0) or virtual (:99) displays."""

    def __init__(self, default_display: str = ":99"):
        self.default_display = default_display

    def _get_display(self, target_display: Optional[str] = None) -> str:
        """Resolve the effective X11 display."""
        return target_display or self.default_display

    def _run_xdotool(self, args: Sequence[str], target_display: Optional[str] = None) -> None:
        """Execute an xdotool command directed to a specific display."""
        disp = self._get_display(target_display)
        cmd = ["xdotool"]
        cmd.extend(args)

        env = os.environ.copy()
        if disp:
            env["DISPLAY"] = disp

        try:
            res = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5.0,
            )
            if res.returncode != 0:
                raise InputDriverError(
                    f"xdotool failed (code {res.returncode}) on display {disp}: {res.stderr.strip()}"
                )
        except subprocess.TimeoutExpired:
            raise InputDriverError(f"xdotool command timed out on display {disp}")
        except FileNotFoundError:
            raise InputDriverError("xdotool binary not found on the system.")

    # ---------------------------------------------------------
    # Mouse Operations
    # ---------------------------------------------------------

    def move(self, x: int, y: int, display: Optional[str] = None) -> None:
        """Move cursor to coordinate (x, y)."""
        logger.debug("Moving cursor to (%d, %d) on %s", x, y, self._get_display(display))
        self._run_xdotool(["mousemove", str(x), str(y)], target_display=display)

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "1",
        clicks: int = 1,
        display: Optional[str] = None,
    ) -> None:
        """Click mouse button at current or specified coordinate."""
        if x is not None and y is not None:
            self.move(x, y, display=display)

        btn_map = {"left": "1", "middle": "2", "right": "3", "1": "1", "2": "2", "3": "3"}
        btn_code = btn_map.get(str(button).lower(), "1")

        args = ["click", "--repeat", str(clicks), btn_code]
        logger.debug("Clicking button %s (%d times) on %s", btn_code, clicks, self._get_display(display))
        self._run_xdotool(args, target_display=display)

    def double_click(self, x: int, y: int, display: Optional[str] = None) -> None:
        """Double click primary button at (x, y)."""
        self.click(x=x, y=y, button="1", clicks=2, display=display)

    def right_click(self, x: int, y: int, display: Optional[str] = None) -> None:
        """Right click at (x, y)."""
        self.click(x=x, y=y, button="3", clicks=1, display=display)

    def mouse_down(self, button: str = "1", display: Optional[str] = None) -> None:
        """Press and hold mouse button."""
        btn_map = {"left": "1", "middle": "2", "right": "3", "1": "1", "2": "2", "3": "3"}
        self._run_xdotool(["mousedown", btn_map.get(str(button).lower(), "1")], target_display=display)

    def mouse_up(self, button: str = "1", display: Optional[str] = None) -> None:
        """Release mouse button."""
        btn_map = {"left": "1", "middle": "2", "right": "3", "1": "1", "2": "2", "3": "3"}
        self._run_xdotool(["mouseup", btn_map.get(str(button).lower(), "1")], target_display=display)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, display: Optional[str] = None) -> None:
        """Drag mouse from start coordinate to end coordinate."""
        logger.debug("Dragging from (%d, %d) to (%d, %d)", start_x, start_y, end_x, end_y)
        self.move(start_x, start_y, display=display)
        self.mouse_down("1", display=display)
        self.move(end_x, end_y, display=display)
        self.mouse_up("1", display=display)

    def scroll(self, direction: str = "down", clicks: int = 3, display: Optional[str] = None) -> None:
        """Scroll mouse wheel. Button 4 is Up, Button 5 is Down in X11."""
        btn_code = "5" if direction.lower() == "down" else "4"
        logger.debug("Scrolling %s (%d clicks)", direction, clicks)
        self._run_xdotool(["click", "--repeat", str(clicks), btn_code], target_display=display)

    # ---------------------------------------------------------
    # Keyboard Operations
    # ---------------------------------------------------------

    def type_text(self, text: str, delay_ms: int = 12, display: Optional[str] = None) -> None:
        """Type unicode text into currently focused element."""
        logger.debug("Typing text (length %d) on %s", len(text), self._get_display(display))
        self._run_xdotool(["type", "--delay", str(delay_ms), text], target_display=display)

    def press_key(self, key: str, display: Optional[str] = None) -> None:
        """Press and release a single key (e.g. 'Return', 'BackSpace', 'Tab')."""
        logger.debug("Pressing key: %s on %s", key, self._get_display(display))
        self._run_xdotool(["key", key], target_display=display)

    def hotkey(self, *keys: str, display: Optional[str] = None) -> None:
        """Trigger a key combination (e.g. 'ctrl+c', 'ctrl+shift+t')."""
        combination = "+".join(keys)
        logger.debug("Triggering hotkey: %s on %s", combination, self._get_display(display))
        self._run_xdotool(["key", combination], target_display=display)
