"""Virtual display management using Xvfb on Linux."""

import logging
import os
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("igris.action.virtual_display")


def _get_x11_socket_path(display_num: int) -> Path:
    """Resolve the X11 domain socket path using secure system temporary directory resolution."""
    base_tmp = Path(tempfile.gettempdir()).resolve()
    return base_tmp / ".X11-unix" / f"X{display_num}"


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
        return _get_x11_socket_path(self.display_number)

    def is_active(self) -> bool:
        """Check if the X server is running and responsive."""
        # Probe responsiveness via xdpyinfo if available
        try:
            res = subprocess.run(
                ["xdpyinfo", "-display", self.display],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=0.8,
            )
            if res.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Probe responsiveness via Unix domain socket connection
        sock = self.socket_path
        if sock.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(0.3)
                    s.connect(str(sock))
                    return True
            except (OSError, socket.error):
                return False

        return False

    @staticmethod
    def find_free_display(start: int = 99, max_search: int = 20) -> str:
        """Find the next free X display number using socket and responsiveness testing."""
        for d in range(start, start + max_search):
            sock = _get_x11_socket_path(d)
            if not sock.exists():
                try:
                    res = subprocess.run(
                        ["xdpyinfo", "-display", f":{d}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=0.3,
                    )
                    if res.returncode != 0:
                        return f":{d}"
                except (subprocess.TimeoutExpired, FileNotFoundError):
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
        """Terminate the Xvfb process."""
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
