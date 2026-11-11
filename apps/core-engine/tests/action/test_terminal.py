"""Tests for AsyncTerminalRunner."""

import pytest
from igris.action.terminal import AsyncTerminalRunner, TerminalSecurityError


@pytest.mark.asyncio
async def test_terminal_runner_basic():
    """Verify standard bash command execution."""
    runner = AsyncTerminalRunner()
    result = await runner.run("echo 'Igris Action Engine'")
    assert result.is_success
    assert "Igris Action Engine" in result.stdout.strip()
    assert result.returncode == 0
    assert result.duration_seconds >= 0


@pytest.mark.asyncio
async def test_terminal_runner_timeout():
    """Verify timeout kills hanging process."""
    runner = AsyncTerminalRunner()
    result = await runner.run("sleep 3", timeout=0.5)
    assert not result.is_success
    assert result.returncode == -1
    assert "timed out" in result.stderr.lower()


@pytest.mark.asyncio
async def test_terminal_security_block():
    """Verify that dangerous destructive commands are blocked by policy."""
    runner = AsyncTerminalRunner()

    with pytest.raises(TerminalSecurityError):
        await runner.run("rm -rf /")

    with pytest.raises(TerminalSecurityError):
        await runner.run("rm -rf /*")

    with pytest.raises(TerminalSecurityError):
        await runner.run("mkfs.ext4 /dev/sda1")
