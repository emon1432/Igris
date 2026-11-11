"""Hybrid coordinate scaling and snap-to-center resolution engine."""

import logging
from typing import List, Optional, Tuple
from pydantic import BaseModel
from igris.perception.accessibility import AccessibleElement

logger = logging.getLogger("igris.perception.resolver")


class ResolvedTarget(BaseModel):
    """Result of coordinate scaling and optional AT-SPI snap-to-center resolution."""
    target_x: int
    target_y: int
    snapped: bool = False
    matched_element: Optional[AccessibleElement] = None
    original_x: int
    original_y: int


class CoordinateResolver:
    """Translates normalized VLM spatial coordinates to physical screen pixels with AT-SPI snapping."""

    def __init__(self, snap_radius_px: int = 35):
        self.snap_radius_px = snap_radius_px

    @staticmethod
    def normalize_to_pixels(
        norm_x: int,
        norm_y: int,
        display_width: int,
        display_height: int,
    ) -> Tuple[int, int]:
        """Convert [0, 1000] normalized model coordinates to physical pixel dimensions."""
        clamped_x = max(0, min(1000, norm_x))
        clamped_y = max(0, min(1000, norm_y))

        px_x = int((clamped_x / 1000.0) * display_width)
        px_y = int((clamped_y / 1000.0) * display_height)

        # Ensure within bounds
        px_x = min(px_x, display_width - 1)
        px_y = min(px_y, display_height - 1)

        return px_x, px_y

    @staticmethod
    def pixels_to_normalize(
        px_x: int,
        px_y: int,
        display_width: int,
        display_height: int,
    ) -> Tuple[int, int]:
        """Convert physical pixel coordinates to [0, 1000] normalized space."""
        if display_width <= 0 or display_height <= 0:
            return 0, 0
        norm_x = int((px_x / display_width) * 1000.0)
        norm_y = int((px_y / display_height) * 1000.0)
        return max(0, min(1000, norm_x)), max(0, min(1000, norm_y))

    def resolve(
        self,
        norm_x: int,
        norm_y: int,
        display_width: int,
        display_height: int,
        accessible_elements: Optional[List[AccessibleElement]] = None,
    ) -> ResolvedTarget:
        """Resolve normalized coordinates into exact click points, snapping to elements if available."""
        orig_x, orig_y = self.normalize_to_pixels(norm_x, norm_y, display_width, display_height)

        if not accessible_elements:
            return ResolvedTarget(
                target_x=orig_x,
                target_y=orig_y,
                snapped=False,
                original_x=orig_x,
                original_y=orig_y,
            )

        # Step 1: Check if (orig_x, orig_y) is directly inside any accessible bounding box
        containing = [elem for elem in accessible_elements if elem.contains(orig_x, orig_y)]
        if containing:
            # Pick smallest bounding box (most specific child element)
            best_element = min(containing, key=lambda e: e.width * e.height)
            snap_x, snap_y = best_element.center
            logger.debug(
                "Snapped (%d, %d) to containing element '%s' [%s] center (%d, %d)",
                orig_x,
                orig_y,
                best_element.name,
                best_element.role,
                snap_x,
                snap_y,
            )
            return ResolvedTarget(
                target_x=snap_x,
                target_y=snap_y,
                snapped=True,
                matched_element=best_element,
                original_x=orig_x,
                original_y=orig_y,
            )

        # Step 2: Check nearby elements within snap_radius_px
        nearby = [
            elem for elem in accessible_elements
            if elem.distance_to(orig_x, orig_y) <= self.snap_radius_px
        ]
        if nearby:
            best_element = min(nearby, key=lambda e: e.distance_to(orig_x, orig_y))
            snap_x, snap_y = best_element.center
            logger.debug(
                "Snapped (%d, %d) to nearest element '%s' [%s] center (%d, %d)",
                orig_x,
                orig_y,
                best_element.name,
                best_element.role,
                snap_x,
                snap_y,
            )
            return ResolvedTarget(
                target_x=snap_x,
                target_y=snap_y,
                snapped=True,
                matched_element=best_element,
                original_x=orig_x,
                original_y=orig_y,
            )

        # Fallback to direct raw pixel mapping
        return ResolvedTarget(
            target_x=orig_x,
            target_y=orig_y,
            snapped=False,
            original_x=orig_x,
            original_y=orig_y,
        )

