"""Tests for AccessibilityInspector (AT-SPI)."""

from igris.perception.accessibility import AccessibleElement, AccessibilityInspector


def test_accessibility_inspector_synthetic_queries():
    """Verify text search and spatial proximity algorithms."""
    inspector = AccessibilityInspector()

    elem1 = AccessibleElement(name="Login Button", role="push button", x=100, y=100, width=80, height=30)
    elem2 = AccessibleElement(name="Email Input", role="entry", x=100, y=50, width=200, height=35)
    elem3 = AccessibleElement(name="Cancel", role="push button", x=200, y=100, width=80, height=30)

    pool = [elem1, elem2, elem3]

    # Search by text
    matches = inspector.find_by_text("email", elements=pool)
    assert len(matches) == 1
    assert matches[0].name == "Email Input"

    # Search by proximity
    closest = inspector.find_closest(110, 95, max_radius=30, elements=pool)
    assert closest is not None
    assert closest.name == "Login Button"


def test_accessibility_inspector_live_query():
    """Verify live AT-SPI traversal does not raise exceptions."""
    inspector = AccessibilityInspector()
    assert inspector.is_available()

    # Query elements (should safely return list without exceptions)
    elements = inspector.get_elements(max_depth=3)
    assert isinstance(elements, list)

