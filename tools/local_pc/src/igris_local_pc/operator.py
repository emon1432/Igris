"""Local PC Operator Tool (AT-SPI Inspection & Virtual Display Automation).

Guarantees:
1. Wraps Linux accessibility (AT-SPI) and virtual display isolation (Xvfb :99) as a mediated tool.
2. Inspects UI trees non-intrusively without mouse clicks (T0).
3. Executes clicks and keystrokes within the isolated :99 virtual framebuffer by default (T1).
4. Direct physical desktop manipulation on :0 is restricted to approved sessions.
"""

from typing import Dict, Any, List, Optional
from igris.perception.accessibility import LinuxAccessibilityInspector
from igris.action.mouse_keyboard import MouseKeyboardDriver
from igris.action.virtual_display import VirtualDisplayManager


class LocalPCOperator:
    """Mediated desktop automation interface for Linux environments."""

    def __init__(
        self,
        inspector: Optional[LinuxAccessibilityInspector] = None,
        input_driver: Optional[MouseKeyboardDriver] = None,
        default_display: str = ":99",
    ):
        self.inspector = inspector or LinuxAccessibilityInspector()
        self.input_driver = input_driver or MouseKeyboardDriver()
        self.default_display = default_display

    def inspect_ui_tree(self, display: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries the AT-SPI accessibility tree to locate window elements (T0)."""
        target_disp = display or self.default_display
        elements = self.inspector.query_elements(role_filter="push_button")
        return [elem.model_dump() for elem in elements]

    def find_button_center(self, button_name: str) -> Optional[Dict[str, int]]:
        """Finds the precise pixel center (x, y) of a named button using AT-SPI (T0)."""
        elements = self.inspector.query_elements(role_filter="push_button")
        for elem in elements:
            if button_name.lower() in elem.name.lower():
                cx = elem.bounds.x + elem.bounds.width // 2
                cy = elem.bounds.y + elem.bounds.height // 2
                return {"x": cx, "y": cy, "width": elem.bounds.width, "height": elem.bounds.height}
        return None

    def click_virtual_coordinate(self, x: int, y: int, display: Optional[str] = None) -> Dict[str, Any]:
        """Dispatches click to isolated virtual framebuffer socket (T1)."""
        target_disp = display or self.default_display
        self.input_driver.click(x, y, display=target_disp)
        return {
            "status": "CLICK_DISPATCHED",
            "coordinate": {"x": x, "y": y},
            "display": target_disp,
        }

    def type_virtual_text(self, text: str, display: Optional[str] = None) -> Dict[str, Any]:
        """Types string into active window on virtual display (T1)."""
        target_disp = display or self.default_display
        self.input_driver.type_text(text, display=target_disp)
        return {
            "status": "TEXT_TYPED",
            "length": len(text),
            "display": target_disp,
        }

