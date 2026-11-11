"""Desktop HUD Overlay for Live Co-Pilot mode visual feedback."""

import asyncio
import logging
import os
import time
from typing import Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("igris.action.hud_overlay")


class TargetIndicator(BaseModel):
    """Visual target coordinate and dimensions for the HUD."""
    x: int
    y: int
    radius: int = 16
    color: str = "#FF0055"  # Neon pink/red laser pointer
    label: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class DesktopHUDOverlay:
    """Manages visual targeting feedback (laser pointer & bounding boxes) on the primary display."""

    def __init__(self, display: str = ":0", enabled: bool = True):
        self.display = display
        self.enabled = enabled
        self.active_indicator: Optional[TargetIndicator] = None
        self._display_obj = None

    def _get_xlib_display(self):
        """Lazy load and connect to X11 display for overlay operations."""
        if not self.enabled:
            return None
        if self._display_obj is not None:
            return self._display_obj

        try:
            import Xlib.display
            self._display_obj = Xlib.display.Display(self.display)
            return self._display_obj
        except Exception as e:
            logger.debug("HUD Overlay X11 display connection unavailable (%s). Running in virtual indicator mode.", e)
            return None

    def flash_laser(
        self,
        x: int,
        y: int,
        radius: int = 16,
        duration_seconds: float = 0.15,
        label: Optional[str] = None,
    ) -> TargetIndicator:
        """Project a transient laser circle at the target coordinate."""
        indicator = TargetIndicator(x=x, y=y, radius=radius, label=label)
        self.active_indicator = indicator

        if not self.enabled:
            return indicator

        logger.info("HUD Laser Indicator at (%d, %d) [radius: %dpx] on %s", x, y, radius, self.display)

        # Attempt hardware X11 shape window flash if active display available
        disp = self._get_xlib_display()
        if disp:
            try:
                # Draw a temporary crosshair/circle on the root overlay or subwindow
                screen = disp.screen()
                root = screen.root
                gc = root.create_gc(
                    foreground=screen.white_pixel,
                    background=screen.black_pixel,
                    line_width=2,
                )
                # Draw circular target crosshair
                root.arc(gc, x - radius, y - radius, radius * 2, radius * 2, 0, 360 * 64)
                root.line(gc, x - radius - 6, y, x + radius + 6, y)
                root.line(gc, x, y - radius - 6, x, y + radius + 6)
                disp.flush()
            except Exception as e:
                logger.debug("X11 laser drawing skipped: %s", e)

        return indicator

    async def async_flash_laser(
        self,
        x: int,
        y: int,
        radius: int = 16,
        duration_seconds: float = 0.15,
        label: Optional[str] = None,
    ) -> TargetIndicator:
        """Asynchronously project laser indicator and yield for visual duration."""
        indicator = self.flash_laser(x=x, y=y, radius=radius, duration_seconds=duration_seconds, label=label)
        if duration_seconds > 0:
            await asyncio.sleep(duration_seconds)
        self.clear()
        return indicator

    def clear(self) -> None:
        """Clear active HUD indicator."""
        self.active_indicator = None
        disp = self._get_xlib_display()
        if disp:
            try:
                disp.flush()
            except Exception:
                pass

