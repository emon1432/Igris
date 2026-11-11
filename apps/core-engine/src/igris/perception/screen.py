"""High-speed screen frame grabber using MSS."""

import base64
import io
import logging
import os
import time
from typing import Optional
import mss
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("igris.perception.screen")


class ScreenFrame(BaseModel):
    """Captured desktop visual frame with metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    width: int
    height: int
    display: str
    duration_ms: float
    timestamp: float = Field(default_factory=time.time)
    raw_image: Image.Image

    def to_bytes(self, format: str = "PNG", quality: int = 85) -> bytes:
        """Convert PIL Image to binary bytes."""
        buffer = io.BytesIO()
        if format.upper() in ["JPG", "JPEG"]:
            # Ensure RGB without alpha channel for JPEG
            img = self.raw_image.convert("RGB")
            img.save(buffer, format="JPEG", quality=quality)
        else:
            self.raw_image.save(buffer, format="PNG")
        return buffer.getvalue()

    def to_base64(self, format: str = "PNG") -> str:
        """Encode image as base64 data string."""
        return base64.b64encode(self.to_bytes(format=format)).decode("utf-8")

    def save(self, filepath: str, format: Optional[str] = None) -> None:
        """Save frame to disk."""
        self.raw_image.save(filepath, format=format)
        logger.debug("Frame saved to %s", filepath)

    def downscale(self, max_dimension: int = 1920) -> "ScreenFrame":
        """Downscale frame if width or height exceeds max_dimension, preserving aspect ratio."""
        if self.width <= max_dimension and self.height <= max_dimension:
            return self

        ratio = min(max_dimension / self.width, max_dimension / self.height)
        new_width = int(self.width * ratio)
        new_height = int(self.height * ratio)

        resized = self.raw_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return ScreenFrame(
            width=new_width,
            height=new_height,
            display=self.display,
            duration_ms=self.duration_ms,
            timestamp=self.timestamp,
            raw_image=resized,
        )


class ScreenCaptureEngine:
    """Manages high-speed desktop frame grabbing across primary and virtual displays."""

    def __init__(self, default_display: str = ":0"):
        self.default_display = default_display

    def capture(self, display: Optional[str] = None, monitor_index: int = 0) -> ScreenFrame:
        """Capture full screen or specific monitor index on target display."""
        target_display = display or self.default_display
        env_backup = os.environ.get("DISPLAY")
        os.environ["DISPLAY"] = target_display

        start_time = time.perf_counter()
        try:
            with mss.MSS() as sct:
                monitors = sct.monitors
                if not monitors:
                    raise RuntimeError(f"No monitors found on display {target_display}")

                # monitor_index 0 is the full unified virtual bounding box
                monitor = monitors[monitor_index if monitor_index < len(monitors) else 0]
                shot = sct.grab(monitor)

                # Convert BGRA raw buffer to PIL RGB Image
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                duration = (time.perf_counter() - start_time) * 1000.0

                logger.debug(
                    "Captured frame on %s (%dx%d) in %.2fms",
                    target_display,
                    shot.width,
                    shot.height,
                    duration,
                )

                return ScreenFrame(
                    width=shot.width,
                    height=shot.height,
                    display=target_display,
                    duration_ms=duration,
                    raw_image=img,
                )
        finally:
            if env_backup is not None:
                os.environ["DISPLAY"] = env_backup
            elif "DISPLAY" in os.environ and display:
                del os.environ["DISPLAY"]

