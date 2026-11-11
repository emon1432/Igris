"""Virtual display management using Xvfb on Linux."""

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("igris.action.virtual_display")


class VirtualDisplayError(Exception):
    """Raised when virtual display operations fail."""
    pass


class VirtualDisplayManager:
    """Manages the lifecycle of an isolated Xvfb virtual framebuffer display."""

    def __init__(
        self,
        display: str = ":99",
        width: int = 1920,
        height: int = 1080,
        depth: int = 24,
    ):
        self.display = display
        self.width = width
        self.height = height
        self.depth = depth
        self.process: Optional[subprocess.Popen] = None
        self._is_running = False

    @property
    def display_number(self) -> int:
        """Extract the numeric display index from string (e.g. ':99' -> 99)."""
        clean = self.display.lstrip(":")
        try:
            return int(clean)
        except ValueError:
            raise VirtualDisplayError(f"Invalid display format: {self.display}")

    @property
    def socket_path(self) -> Path:
        """Return the expected X11 Unix socket path."""
        return Path(f"/tmp/.X11-unix/X{self.display_number}")

    @property
    def lock_path(self) -> Path:
        """Return the X11 lock file path."""
        return Path(f"/tmp/.X{self.display_number}-lock")

    def is_active(self) -> bool:
        """Check if the X server socket exists and is responsive."""
        if not self.socket_path.exists():
            return False

        # Verify using xdpyinfo if available, or socket connectivity check
        try:
            res = subprocess.run(
                ["xdpyinfo", "-display", self.display],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1,
            )
            return res.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to checking socket existence
            return self.socket_path.exists()

    @staticmethod
    def find_free_display(start: int = 99, max_search: int = 20) -> str:
        """Find the next free X display number."""
        for d in range(start, start + max_search):
            sock = Path(f"/tmp/.X11-unix/X{d}")
            lock = Path(f"/tmp/.X{d}-lock")
            if not sock.exists() and not lock.exists():
                return f":{d}"
        raise VirtualDisplayError("No free virtual displays found in search range.")

    def start(self, timeout_seconds: float = 5.0) -> None:
        """Start the Xvfb virtual display process."""
        if self._is_running or self.is_active():
            logger.info("Virtual display %s is already running.", self.display)
            self._is_running = True
            return

        cmd = [
            "Xvfb",
            self.display,
            "-screen",
            "0",
            f"{self.width}x{self.height}x{self.depth}",
            "-ac",
            "+extension",
            "GLX",
            "+render",
            "-noreset",
        ]

        logger.info("Starting Xvfb: %s", " ".join(cmd))
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
        except FileNotFoundError:
            raise VirtualDisplayError(
                "Xvfb binary not found. Please ensure xvfb is installed on the system."
            )

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Check if process exited prematurely
            if self.process.poll() is not None:
                stderr_output = ""
                if self.process.stderr:
                    stderr_output = self.process.stderr.read().decode("utf-8", errors="replace")
                raise VirtualDisplayError(
                    f"Xvfb process terminated unexpectedly (code {self.process.returncode}): {stderr_output}"
                )

            if self.socket_path.exists():
                self._is_running = True
                logger.info(
                    "Virtual display %s successfully initialized (%dx%dx%d).",
                    self.display,
                    self.width,
                    self.height,
                    self.depth,
                )
                return

            time.sleep(0.1)

        self.stop()
        raise VirtualDisplayError(
            f"Timed out waiting for virtual display {self.display} socket to initialize."
        )

    def stop(self) -> None:
        """Terminate the Xvfb process and clean up sockets."""
        if self.process:
            logger.info("Stopping virtual display %s (PID %s)...", self.display, self.process.pid)
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=2.0)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.process = None

        self._is_running = False

        # Clean lingering lock files if safe
        if self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except OSError:
                pass

        logger.info("Virtual display %s stopped.", self.display)

    def __enter__(self) -> "VirtualDisplayManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    async def __aenter__(self) -> "VirtualDisplayManager":
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
