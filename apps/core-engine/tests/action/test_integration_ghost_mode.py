"""End-to-End Ghost Mode Integration Test."""

import os
from pathlib import Path
import mss
from igris.action.virtual_display import VirtualDisplayManager
from igris.action.mouse_keyboard import InputDriver
from igris.action.terminal import AsyncTerminalRunner


def test_ghost_mode_screenshot_capture(tmp_path: Path):
    """Verify that an application can run headlessly and be captured via mss without touching :0."""
    display = VirtualDisplayManager.find_free_display(start=94)
    manager = VirtualDisplayManager(display=display, width=1920, height=1080)

    with manager:
        driver = InputDriver(default_display=display)
        # Perform mouse movement and keystrokes on the virtual display
        driver.move(960, 540)
        driver.click(960, 540)
        driver.type_text("Igris Ghost Engine Online")

        # Capture virtual display frame via mss
        screenshot_path = tmp_path / "ghost_frame.png"
        os.environ["DISPLAY"] = display

        with mss.MSS() as sct:
            monitors = sct.monitors
            assert len(monitors) > 0
            # Grab full screen (monitor 0)
            shot = sct.grab(monitors[0])
            mss.tools.to_png(shot.rgb, shot.size, output=str(screenshot_path))

        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0
        assert shot.width == 1920
        assert shot.height == 1080
