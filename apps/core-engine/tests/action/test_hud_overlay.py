"""Tests for Desktop HUD Overlay and visual feedback."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from igris.action.hud_overlay import DesktopHUDOverlay, TargetIndicator
from igris.brain.dispatcher import ActionDispatcher
from igris.brain.vlm_client import VisualAction
from igris.perception.resolver import CoordinateResolver, ResolvedTarget


def test_target_indicator_model():
    """Verify target indicator schema and default attributes."""
    indicator = TargetIndicator(x=500, y=300, radius=20, label="Search Button")
    assert indicator.x == 500
    assert indicator.y == 300
    assert indicator.radius == 20
    assert indicator.color == "#FF0055"
    assert indicator.label == "Search Button"


def test_hud_overlay_flash_and_clear():
    """Verify flash laser indicator and clear functionality."""
    hud = DesktopHUDOverlay(display=":0", enabled=True)
    indicator = hud.flash_laser(x=200, y=150, radius=12)
    assert indicator.x == 200
    assert indicator.y == 150
    assert hud.active_indicator is not None
    assert hud.active_indicator.x == 200

    hud.clear()
    assert hud.active_indicator is None


@pytest.mark.asyncio
async def test_hud_overlay_async_flash():
    """Verify async flash laser lifecycle."""
    hud = DesktopHUDOverlay(display=":0", enabled=True)
    # Using 0 duration for fast unit test
    indicator = await hud.async_flash_laser(x=100, y=100, duration_seconds=0.01)
    assert indicator.x == 100
    assert hud.active_indicator is None


@pytest.mark.asyncio
async def test_dispatcher_triggers_hud_in_live_mode():
    """Verify ActionDispatcher triggers HUD laser overlay when executing in Live mode (:0)."""
    mock_input = MagicMock()
    mock_resolver = MagicMock(spec=CoordinateResolver)

    mock_resolved = ResolvedTarget(
        target_x=350,
        target_y=250,
        original_x=350,
        original_y=250,
        snapped=False,
        matched_element=None,
    )
    mock_resolver.resolve.return_value = mock_resolved

    mock_hud = MagicMock(spec=DesktopHUDOverlay)
    mock_hud.async_flash_laser = AsyncMock()

    dispatcher = ActionDispatcher(
        input_driver=mock_input,
        coordinate_resolver=mock_resolver,
        hud_overlay=mock_hud,
    )

    action = VisualAction(
        action_type="click",
        normalized_x=350,
        normalized_y=250,
        reasoning="Click on menu item",
    )

    # 1. In Live Mode (:0) -> HUD should be flashed
    res = await dispatcher.dispatch(
        action=action,
        display_width=1920,
        display_height=1080,
        display=":0",
    )
    assert res.success
    mock_hud.async_flash_laser.assert_awaited_once_with(350, 250, duration_seconds=0.1)

    # 2. In Ghost Mode (:99) -> HUD should NOT be flashed
    mock_hud.async_flash_laser.reset_mock()
    res_ghost = await dispatcher.dispatch(
        action=action,
        display_width=1920,
        display_height=1080,
        display=":99",
    )
    assert res_ghost.success
    mock_hud.async_flash_laser.assert_not_awaited()
