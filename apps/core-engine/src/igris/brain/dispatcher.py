"""Action Dispatcher: Translates high-level VisualAction into physical input and system commands."""

import asyncio
import logging
from typing import List, Optional
from pydantic import BaseModel
from igris.action.hud_overlay import DesktopHUDOverlay
from igris.action.mouse_keyboard import InputDriver
from igris.action.terminal import AsyncTerminalRunner
from igris.brain.vlm_client import VisualAction
from igris.perception.accessibility import AccessibleElement, AccessibilityInspector
from igris.perception.resolver import CoordinateResolver, ResolvedTarget

logger = logging.getLogger("igris.brain.dispatcher")


class DispatchResult(BaseModel):
    """Result of dispatching a single action."""
    action_type: str
    success: bool
    resolved_target: Optional[ResolvedTarget] = None
    details: str
    duration_seconds: float = 0.0


class ActionDispatcher:
    """Dispatches VLM actions to mouse, keyboard, or terminal drivers with coordinate resolution."""

    def __init__(
        self,
        input_driver: InputDriver,
        coordinate_resolver: CoordinateResolver,
        terminal_runner: Optional[AsyncTerminalRunner] = None,
        hud_overlay: Optional[DesktopHUDOverlay] = None,
    ):
        self.input_driver = input_driver
        self.resolver = coordinate_resolver
        self.terminal = terminal_runner or AsyncTerminalRunner()
        self.hud_overlay = hud_overlay

    async def dispatch(
        self,
        action: VisualAction,
        display_width: int,
        display_height: int,
        display: str,
        accessible_elements: Optional[List[AccessibleElement]] = None,
    ) -> DispatchResult:
        """Resolve target coordinates and execute the given VisualAction."""
        action_type = action.action_type.lower()
        logger.info("Dispatching action: %s on %s (%s)", action_type, display, action.reasoning)

        # Actions that do not require spatial coordinate resolution
        if action_type in ["wait", "sleep"]:
            await asyncio.sleep(1.0)
            return DispatchResult(
                action_type=action_type,
                success=True,
                details="Waited for UI reaction",
            )

        if action_type == "finished":
            return DispatchResult(
                action_type=action_type,
                success=True,
                details=f"Task completed: {action.reasoning}",
            )

        if action_type == "terminal":
            cmd = action.text_input or ""
            res = await self.terminal.run(cmd, display=display)
            return DispatchResult(
                action_type=action_type,
                success=res.is_success,
                details=f"Ran shell command (code {res.returncode}): {res.stdout.strip()[:100]}",
            )

        # Resolve spatial coordinates with AT-SPI snap-to-center
        resolved = self.resolver.resolve(
            norm_x=action.normalized_x,
            norm_y=action.normalized_y,
            display_width=display_width,
            display_height=display_height,
            accessible_elements=accessible_elements,
        )

        target_x = resolved.target_x
        target_y = resolved.target_y

        # Flash HUD overlay laser indicator if in Live mode (:0)
        if self.hud_overlay and display == ":0":
            await self.hud_overlay.async_flash_laser(target_x, target_y, duration_seconds=0.1)

        try:
            if action_type in ["click", "left_click"]:
                self.input_driver.click(x=target_x, y=target_y, button="1", display=display)
                details = f"Clicked at ({target_x}, {target_y})"
                if resolved.snapped and resolved.matched_element:
                    details += f" [Snapped to '{resolved.matched_element.name}']"

            elif action_type == "double_click":
                self.input_driver.double_click(x=target_x, y=target_y, display=display)
                details = f"Double-clicked at ({target_x}, {target_y})"

            elif action_type in ["right_click", "context_click"]:
                self.input_driver.right_click(x=target_x, y=target_y, display=display)
                details = f"Right-clicked at ({target_x}, {target_y})"

            elif action_type in ["type", "input", "type_and_enter"]:
                # Click target first to focus if coordinate specified, then type text
                if action.normalized_x > 0 or action.normalized_y > 0:
                    self.input_driver.click(x=target_x, y=target_y, button="1", display=display)
                    await asyncio.sleep(0.1)

                text_to_type = action.text_input or ""
                self.input_driver.type_text(text_to_type, display=display)
                if action_type == "type_and_enter" or text_to_type.endswith("\n"):
                    self.input_driver.press_key("Return", display=display)
                details = f"Typed text '{text_to_type}' into ({target_x}, {target_y})"

            elif action_type in ["press_key", "key"]:
                key_name = action.text_input or "Return"
                if key_name.lower() in ["enter", "return"]:
                    key_name = "Return"
                self.input_driver.press_key(key_name, display=display)
                details = f"Pressed key '{key_name}'"

            elif action_type in ["hotkey"]:
                keys = [k.strip() for k in (action.text_input or "").split("+") if k.strip()]
                if keys:
                    self.input_driver.hotkey(*keys, display=display)
                details = f"Triggered hotkey '{action.text_input}'"

            elif action_type in ["scroll_down", "scroll"]:
                self.input_driver.move(target_x, target_y, display=display)
                self.input_driver.scroll(direction="down", clicks=3, display=display)
                details = f"Scrolled down at ({target_x}, {target_y})"

            elif action_type == "scroll_up":
                self.input_driver.move(target_x, target_y, display=display)
                self.input_driver.scroll(direction="up", clicks=3, display=display)
                details = f"Scrolled up at ({target_x}, {target_y})"

            else:
                logger.warning("Unrecognized action type: %s. Performing fallback click.", action_type)
                self.input_driver.click(x=target_x, y=target_y, display=display)
                details = f"Fallback click at ({target_x}, {target_y})"

            return DispatchResult(
                action_type=action_type,
                success=True,
                resolved_target=resolved,
                details=details,
            )

        except Exception as exc:
            logger.error("Failed to execute action %s: %s", action_type, exc)
            return DispatchResult(
                action_type=action_type,
                success=False,
                resolved_target=resolved,
                details=f"Execution error: {exc}",
            )

