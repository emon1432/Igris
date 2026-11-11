"""Tests for ScreenCaptureEngine."""

import pytest
from igris.action.virtual_display import VirtualDisplayManager
from igris.perception.screen import ScreenCaptureEngine, ScreenFrame


@pytest.fixture(scope="module")
def virtual_display():
    """Start an isolated virtual display for frame grabbing tests."""
    display = VirtualDisplayManager.find_free_display(start=93)
    mgr = VirtualDisplayManager(display=display, width=1920, height=1080)
    mgr.start(timeout_seconds=5.0)
    yield display
    mgr.stop()


def test_screen_capture_properties(virtual_display):
    """Verify that screen capture produces valid dimensions, byte payloads, and fast latency."""
    engine = ScreenCaptureEngine(default_display=virtual_display)
    frame = engine.capture()

    assert isinstance(frame, ScreenFrame)
    assert frame.width == 1920
    assert frame.height == 1080
    assert frame.display == virtual_display
    assert frame.duration_ms > 0
    assert frame.duration_ms < 50.0  # Fast capture assertion

    # Format conversions
    png_bytes = frame.to_bytes(format="PNG")
    assert len(png_bytes) > 0

    jpeg_bytes = frame.to_bytes(format="JPEG")
    assert len(jpeg_bytes) > 0

    b64 = frame.to_base64(format="PNG")
    assert len(b64) > 0
    assert isinstance(b64, str)


def test_screen_frame_downscale(virtual_display):
    """Verify aspect-ratio preserving frame downscaling."""
    engine = ScreenCaptureEngine(default_display=virtual_display)
    frame = engine.capture()

    downscaled = frame.downscale(max_dimension=960)
    assert downscaled.width == 960
    assert downscaled.height == 540  # 16:9 ratio preserved

