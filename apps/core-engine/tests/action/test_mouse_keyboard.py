"""Tests for InputDriver (Mouse and Keyboard event injection)."""

import pytest
from igris.action.virtual_display import VirtualDisplayManager
from igris.action.mouse_keyboard import InputDriver


@pytest.fixture(scope="module")
def virtual_x11():
    """Spin up an isolated Xvfb display for input testing."""
    display = VirtualDisplayManager.find_free_display(start=98)
    manager = VirtualDisplayManager(display=display, width=1920, height=1080)
    manager.start(timeout_seconds=5.0)
    yield display
    manager.stop()


def test_mouse_move_and_clicks(virtual_x11):
    """Verify mouse positioning and click dispatches on virtual display."""
    driver = InputDriver(default_display=virtual_x11)

    driver.move(500, 400)
    driver.click(x=300, y=200, button="left", clicks=1)
    driver.double_click(x=300, y=200)
    driver.right_click(x=300, y=200)
    driver.drag(start_x=100, start_y=100, end_x=200, end_y=200)
    driver.scroll(direction="down", clicks=2)
    driver.scroll(direction="up", clicks=2)


def test_keyboard_typing_and_hotkeys(virtual_x11):
    """Verify text typing and hotkey dispatches on virtual display."""
    driver = InputDriver(default_display=virtual_x11)

    driver.type_text("Hello Igris 2026", delay_ms=5)
    driver.press_key("Return")
    driver.hotkey("ctrl", "a")
    driver.hotkey("ctrl", "c")
