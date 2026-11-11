"""Tests for CoordinateResolver."""

from igris.perception.accessibility import AccessibleElement
from igris.perception.resolver import CoordinateResolver


def test_normalize_to_pixels_scaling():
    """Verify coordinate scaling to display resolutions."""
    # Screen center
    px_x, px_y = CoordinateResolver.normalize_to_pixels(500, 500, 1920, 1080)
    assert px_x == 960
    assert px_y == 540

    # Top-left corner
    tl_x, tl_y = CoordinateResolver.normalize_to_pixels(0, 0, 1920, 1080)
    assert tl_x == 0
    assert tl_y == 0

    # Bottom-right corner (clamped within display bounds)
    br_x, br_y = CoordinateResolver.normalize_to_pixels(1000, 1000, 1920, 1080)
    assert br_x == 1919
    assert br_y == 1079


def test_snap_to_containing_element():
    """Verify snap-to-center when coordinate lands inside an accessible element."""
    resolver = CoordinateResolver(snap_radius_px=30)

    # Button at x=400, y=300 with width=100, height=50 (Center is 450, 325)
    button = AccessibleElement(
        name="Submit Order",
        role="push button",
        x=400,
        y=300,
        width=100,
        height=50,
    )

    # Point inside button: x=420, y=310
    norm_x, norm_y = CoordinateResolver.pixels_to_normalize(420, 310, 1000, 1000)

    resolved = resolver.resolve(
        norm_x=norm_x,
        norm_y=norm_y,
        display_width=1000,
        display_height=1000,
        accessible_elements=[button],
    )

    assert resolved.snapped
    assert resolved.target_x == 450
    assert resolved.target_y == 325
    assert resolved.matched_element.name == "Submit Order"


def test_snap_to_nearby_element():
    """Verify snap-to-center when coordinate lands slightly outside but within radius."""
    resolver = CoordinateResolver(snap_radius_px=35)

    icon = AccessibleElement(
        name="Search Icon",
        role="icon",
        x=200,
        y=200,
        width=40,
        height=40,
    )  # Center: (220, 220)

    # Point at (245, 220) -> distance to center is 25px (within 35px radius)
    norm_x, norm_y = CoordinateResolver.pixels_to_normalize(245, 220, 1000, 1000)

    resolved = resolver.resolve(
        norm_x=norm_x,
        norm_y=norm_y,
        display_width=1000,
        display_height=1000,
        accessible_elements=[icon],
    )

    assert resolved.snapped
    assert resolved.target_x == 220
    assert resolved.target_y == 220


def test_fallback_when_no_element_nearby():
    """Verify direct raw pixel mapping when no element is near."""
    resolver = CoordinateResolver(snap_radius_px=20)

    button = AccessibleElement(
        name="Far Button",
        role="push button",
        x=100,
        y=100,
        width=50,
        height=30,
    )

    # Point far away at (800, 800)
    norm_x, norm_y = CoordinateResolver.pixels_to_normalize(800, 800, 1000, 1000)

    resolved = resolver.resolve(
        norm_x=norm_x,
        norm_y=norm_y,
        display_width=1000,
        display_height=1000,
        accessible_elements=[button],
    )

    assert not resolved.snapped
    assert resolved.target_x == 800
    assert resolved.target_y == 800
    assert resolved.matched_element is None

