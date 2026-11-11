"""Tests for VirtualDisplayManager (Xvfb lifecycle)."""

import pytest
from igris.action.virtual_display import VirtualDisplayManager


def test_virtual_display_lifecycle():
    """Verify that Xvfb starts, reports active, and shuts down cleanly."""
    display = VirtualDisplayManager.find_free_display(start=95)
    manager = VirtualDisplayManager(display=display, width=1280, height=720, depth=24)

    assert not manager.is_active()

    try:
        manager.start(timeout_seconds=5.0)
        assert manager.is_active()
        assert manager.socket_path.exists()
    finally:
        manager.stop()

    assert not manager.is_active()


def test_virtual_display_context_manager():
    """Verify synchronous context manager protocol."""
    display = VirtualDisplayManager.find_free_display(start=96)
    manager = VirtualDisplayManager(display=display, width=1024, height=768)

    with manager:
        assert manager.is_active()

    assert not manager.is_active()


@pytest.mark.asyncio
async def test_virtual_display_async_context():
    """Verify asynchronous context manager protocol."""
    display = VirtualDisplayManager.find_free_display(start=97)
    manager = VirtualDisplayManager(display=display, width=1024, height=768)

    async with manager:
        assert manager.is_active()

    assert not manager.is_active()
