"""Asynchronous terminal and shell runner for Igris action engine."""

import asyncio
import logging
import os
import re
import time
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger("igris.action.terminal")


class CommandResult(BaseModel):
    """Result of an executed shell command."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def is_success(self) -> bool:
        return self.returncode == 0


class TerminalSecurityError(Exception):
    """Raised when a prohibited destructive shell command is attempted."""
    pass


class AsyncTerminalRunner:
    """Asynchronously executes bash commands with display awareness and safety guardrails."""

    BLOCKED_PATTERNS = [
        re.compile(r"\brm\s+-[a-zA-Z]{1,8}\s+(?:/(?:\*|\s|$|;)|~|\$HOME)"),
        re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\s+"),
        re.compile(r"\bdd\s+if=.*of=/dev/(?:sd[a-z]|nvme[0-9]n[0-9])"),
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),  # fork bomb
    ]

    def __init__(self, default_cwd: Optional[str] = None):
        self.default_cwd = default_cwd or os.getcwd()

    def _validate_command_safety(self, command: str) -> None:
        """Scan command string against critical destructive patterns."""
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.search(command):
                logger.critical("Blocked prohibited destructive command: %s", command)
                raise TerminalSecurityError(
                    f"Command rejected by safety policy: Destructive system impact detected in '{command}'."
                )

    async def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: float = 60.0,
        display: Optional[str] = None,
    ) -> CommandResult:
        """Execute a shell command asynchronously and return stdout/stderr."""
        self._validate_command_safety(command)

        env = os.environ.copy()
        if display:
            env["DISPLAY"] = display

        working_dir = cwd or self.default_cwd
        logger.debug("Executing shell command: '%s' in '%s' (DISPLAY=%s)", command, working_dir, display)

        start_time = time.time()
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=working_dir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            duration = time.time() - start_time
            stdout_str = stdout_data.decode("utf-8", errors="replace")
            stderr_str = stderr_data.decode("utf-8", errors="replace")

            logger.debug("Command finished (code %d) in %.2fs", process.returncode or 0, duration)
            return CommandResult(
                command=command,
                returncode=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_seconds=duration,
            )

        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except ProcessLookupError:
                pass
            duration = time.time() - start_time
            logger.warning("Command timed out after %.2fs: %s", timeout, command)
            return CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds.",
                duration_seconds=duration,
            )
