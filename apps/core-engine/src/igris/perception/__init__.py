"""Perception package for screen frame capture, AT-SPI accessibility, and coordinate resolution."""

from igris.perception.screen import ScreenFrame, ScreenCaptureEngine
from igris.perception.accessibility import AccessibleElement, AccessibilityInspector
from igris.perception.resolver import ResolvedTarget, CoordinateResolver

__all__ = [
    "ScreenFrame",
    "ScreenCaptureEngine",
    "AccessibleElement",
    "AccessibilityInspector",
    "ResolvedTarget",
    "CoordinateResolver",
]
