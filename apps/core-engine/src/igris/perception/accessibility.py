"""Linux Accessibility Tree (AT-SPI) Inspector for deterministic UI element localization."""

import logging
import math
import os
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("igris.perception.accessibility")

# Attempt importing Atspi via PyGObject
HAS_ATSPI = False
try:
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    HAS_ATSPI = True
except Exception as e:
    logger.warning("AT-SPI PyGObject unavailable: %s. Fallback mode active.", e)


class AccessibleElement(BaseModel):
    """Represents an accessible UI component detected on the Linux desktop."""
    name: str = ""
    role: str = ""
    description: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    states: List[str] = Field(default_factory=list)

    @property
    def center(self) -> tuple[int, int]:
        """Return the exact center coordinate (X, Y) of this component."""
        return self.x + (self.width // 2), self.y + (self.height // 2)

    def contains(self, px: int, py: int) -> bool:
        """Check if coordinate (px, py) falls inside this element's bounding box."""
        return self.x <= px <= (self.x + self.width) and self.y <= py <= (self.y + self.height)

    def distance_to(self, px: int, py: int) -> float:
        """Calculate Euclidean distance from (px, py) to the nearest boundary of this element.
        Returns 0.0 if (px, py) is inside the bounding box.
        """
        dx = max(self.x - px, 0, px - (self.x + self.width))
        dy = max(self.y - py, 0, py - (self.y + self.height))
        if dx == 0 and dy == 0:
            return 0.0
        return math.hypot(dx, dy)

    def distance_to_center(self, px: int, py: int) -> float:
        """Calculate Euclidean distance from (px, py) to the center of this element."""
        cx, cy = self.center
        return math.hypot(px - cx, py - cy)


class AccessibilityInspector:
    """Traverses the Linux AT-SPI accessibility bus to inspect visible UI widgets."""

    def __init__(self, default_display: str = ":0"):
        self.default_display = default_display

    def is_available(self) -> bool:
        """Return True if AT-SPI bindings are functional."""
        return HAS_ATSPI

    def get_elements(
        self,
        max_depth: int = 8,
        display: Optional[str] = None,
        only_visible: bool = True,
    ) -> List[AccessibleElement]:
        """Traverse the desktop accessible hierarchy and collect visible interactive elements."""
        if not HAS_ATSPI:
            logger.debug("AT-SPI is not available in current environment.")
            return []

        target_display = display or self.default_display
        env_backup = os.environ.get("DISPLAY")
        if target_display:
            os.environ["DISPLAY"] = target_display

        elements: List[AccessibleElement] = []

        try:
            desktop_count = Atspi.get_desktop_count()
            for d_idx in range(desktop_count):
                desktop = Atspi.get_desktop(d_idx)
                if not desktop:
                    continue
                self._traverse(desktop, elements, depth=0, max_depth=max_depth, only_visible=only_visible)
        except Exception as exc:
            logger.error("Error inspecting AT-SPI tree: %s", exc)
        finally:
            if env_backup is not None:
                os.environ["DISPLAY"] = env_backup
            elif "DISPLAY" in os.environ and display:
                del os.environ["DISPLAY"]

        logger.debug("AT-SPI discovered %d elements on %s", len(elements), target_display)
        return elements

    def _traverse(
        self,
        node,
        elements: List[AccessibleElement],
        depth: int,
        max_depth: int,
        only_visible: bool,
    ) -> None:
        """Recursive helper to inspect child nodes."""
        if depth > max_depth or node is None:
            return

        try:
            role_name = node.get_role_name() or ""
            name = node.get_name() or ""
            description = node.get_description() or ""

            # Check component bounding box
            comp = node.get_component_iface()
            if comp:
                rect = comp.get_extents(Atspi.CoordType.SCREEN)
                x, y, w, h = rect.x, rect.y, rect.width, rect.height

                # Discard non-renderable/zero dimensions
                if w > 0 and h > 0 and x >= 0 and y >= 0:
                    state_set = node.get_state_set()
                    states = []
                    if state_set:
                        # Extract basic state names
                        for s in [
                            Atspi.StateType.SHOWING,
                            Atspi.StateType.VISIBLE,
                            Atspi.StateType.FOCUSED,
                            Atspi.StateType.ENABLED,
                        ]:
                            if state_set.contains(s):
                                states.append(Atspi.state_type_get_name(s))

                    is_visible = "showing" in states or "visible" in states or not only_visible
                    if is_visible:
                        elements.append(
                            AccessibleElement(
                                name=name,
                                role=role_name,
                                description=description,
                                x=x,
                                y=y,
                                width=w,
                                height=h,
                                states=states,
                            )
                        )

            # Traverse children
            child_count = node.get_child_count()
            for i in range(child_count):
                child = node.get_child_at_index(i)
                self._traverse(child, elements, depth + 1, max_depth, only_visible)

        except Exception:
            # Handle transient D-Bus disconnects during navigation
            pass

    def find_by_text(self, query: str, elements: Optional[List[AccessibleElement]] = None) -> List[AccessibleElement]:
        """Find elements whose name or description contains the query string."""
        pool = elements if elements is not None else self.get_elements()
        query_lower = query.lower().strip()
        return [
            elem for elem in pool
            if query_lower in elem.name.lower() or query_lower in elem.description.lower()
        ]

    def find_closest(
        self,
        x: int,
        y: int,
        max_radius: int = 50,
        elements: Optional[List[AccessibleElement]] = None,
    ) -> Optional[AccessibleElement]:
        """Find the nearest interactive element within a search radius."""
        pool = elements if elements is not None else self.get_elements()
        candidates = [elem for elem in pool if elem.distance_to(x, y) <= max_radius]
        if not candidates:
            return None
        return min(candidates, key=lambda elem: elem.distance_to(x, y))
