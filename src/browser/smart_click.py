"""
Smart click utility with multiple fallback strategies for reliable element interaction

Adapted from nodriver skill library for GEO-Perplex project.
Handles edge cases where normal clicking fails by trying multiple approaches.

Features:
- 6 click strategies with automatic fallback
- Element visibility and interactability checks
- Scroll-into-view before clicking
- Human-like delays and positioning
- Click verification support
"""

import asyncio
import random
import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Callable
import nodriver as uc

from src.browser.element_waiter import ElementWaiter, WaitCondition

logger = logging.getLogger(__name__)


class ClickStrategy(Enum):
    """Click strategies in order of preference."""
    NORMAL = "normal"
    JAVASCRIPT = "javascript"
    FOCUS_ENTER = "focus_enter"
    FOCUS_SPACE = "focus_space"
    DISPATCH_EVENT = "dispatch_event"
    DOUBLE_CLICK = "double_click"


@dataclass
class ClickResult:
    """Result of a click attempt."""
    success: bool
    strategy_used: ClickStrategy
    attempts: int
    error: Optional[str] = None
    verification_passed: bool = False


class SmartClicker:
    """
    Handles reliable element clicking with multiple fallback strategies.

    Example:
        clicker = SmartClicker(page=page, verify_click=True)
        result = await clicker.click('#submit-button')
        if result.success:
            print(f"Clicked using {result.strategy_used.value}")
    """

    def __init__(
        self,
        page,
        verify_click: bool = True,
        scroll_into_view: bool = True,
        human_like_delay: bool = True,
        max_retries: int = 6,
    ):
        """
        Initialize the SmartClicker.

        Args:
            page: The nodriver page object
            verify_click: Check if click action had desired effect
            scroll_into_view: Scroll element into viewport before clicking
            human_like_delay: Add random delays between actions
            max_retries: Maximum number of strategies to try
        """
        self.page = page
        self.verify_click = verify_click
        self.scroll_into_view = scroll_into_view
        self.human_like_delay = human_like_delay
        self.max_retries = max_retries

    async def click(
        self,
        selector: str,
        verify_action: Optional[Callable] = None,
        timeout: float = 10.0,
    ) -> ClickResult:
        """
        Click an element with automatic fallback strategies.

        Args:
            selector: CSS selector for the element
            verify_action: Optional async callable to verify click succeeded
            timeout: Timeout for the entire operation

        Returns:
            ClickResult with success status and details
        """
        start_time = time.time()

        try:
            # Step 1: Find and validate element
            element = await self._find_element(selector, timeout)
            if not element:
                return ClickResult(
                    success=False,
                    strategy_used=ClickStrategy.NORMAL,
                    attempts=1,
                    error=f"Element not found: {selector}",
                )

            # Step 2: Check visibility and interactability
            is_visible = await self._check_element_visible(element)
            is_interactable = await self._check_element_interactable(element)

            if not is_visible or not is_interactable:
                logger.warning(
                    f"Element not fully interactable - visible: {is_visible}, "
                    f"interactable: {is_interactable}"
                )

            # Step 3: Scroll into view if needed
            if self.scroll_into_view:
                await self._scroll_into_view(element)
                await self._add_delay(100, 300)

            # Step 4: Try click strategies in order
            strategies = self._get_strategies_to_try()
            for attempt, strategy in enumerate(strategies, 1):
                if time.time() - start_time > timeout:
                    return ClickResult(
                        success=False,
                        strategy_used=strategy,
                        attempts=attempt,
                        error="Timeout exceeded",
                    )

                try:
                    logger.debug(f"Trying click strategy: {strategy.value} (attempt {attempt})")
                    success = await self._execute_click_strategy(element, strategy)
                    if success:
                        await self._add_delay(200, 500)

                        # Verify if requested
                        verified = True
                        if verify_action:
                            verified = await self._verify_action(
                                verify_action, timeout - (time.time() - start_time)
                            )

                        logger.info(f"Click successful using {strategy.value} strategy")
                        return ClickResult(
                            success=True,
                            strategy_used=strategy,
                            attempts=attempt,
                            verification_passed=verified,
                        )
                except Exception as e:
                    logger.debug(f"Strategy {strategy.value} failed: {str(e)}")
                    continue

            return ClickResult(
                success=False,
                strategy_used=strategies[-1],
                attempts=len(strategies),
                error="All strategies failed",
            )

        except Exception as e:
            logger.error(f"Click operation failed: {str(e)}")
            return ClickResult(
                success=False,
                strategy_used=ClickStrategy.NORMAL,
                attempts=0,
                error=str(e),
            )

    def _get_strategies_to_try(self) -> list:
        """Get list of strategies to try in order."""
        return [
            ClickStrategy.NORMAL,
            ClickStrategy.JAVASCRIPT,
            ClickStrategy.FOCUS_ENTER,
            ClickStrategy.DISPATCH_EVENT,
            ClickStrategy.FOCUS_SPACE,
            ClickStrategy.DOUBLE_CLICK,
        ]

    async def _find_element(self, selector: str, timeout: float) -> Any:
        """
        Find element using intelligent ElementWaiter.

        Args:
            selector: CSS selector for element
            timeout: Maximum time to wait in seconds

        Returns:
            Element if found, None otherwise
        """
        # Use ElementWaiter instead of reimplementing
        waiter = ElementWaiter(self.page, poll_interval=0.1, verbose=False)

        # Wait for element to be present
        result = await waiter.wait_for_presence(selector, timeout=timeout)

        if result.success:
            logger.debug(
                f"Element found: {selector} after {result.wait_time:.2f}s "
                f"({result.attempts} attempts)"
            )
            return result.element
        else:
            logger.debug(
                f"Element not found: {selector} after {result.wait_time:.2f}s "
                f"({result.attempts} attempts)"
            )
            return None

    async def _check_element_visible(self, element: Any) -> bool:
        """Check if element is visible in the viewport."""
        try:
            script = """
            function isVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden'
                    || style.opacity === '0') {
                    return false;
                }
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }
            return isVisible(arguments[0]);
            """
            return await self.page.evaluate(script, element)
        except Exception as e:
            logger.debug(f"Error checking visibility: {str(e)}")
            return True  # Assume visible on error

    async def _check_element_interactable(self, element: Any) -> bool:
        """Check if element can receive interactions."""
        try:
            script = """
            function isInteractable(el) {
                if (!el) return false;

                // Check if disabled
                if (el.disabled) return false;

                // Check aria-disabled
                if (el.getAttribute('aria-disabled') === 'true') return false;

                // Check pointer-events
                const style = window.getComputedStyle(el);
                if (style.pointerEvents === 'none') return false;

                // Check if element or parent is hidden
                let current = el;
                while (current) {
                    const s = window.getComputedStyle(current);
                    if (s.display === 'none' || s.visibility === 'hidden') {
                        return false;
                    }
                    current = current.parentElement;
                }

                return true;
            }
            return isInteractable(arguments[0]);
            """
            return await self.page.evaluate(script, element)
        except Exception as e:
            logger.debug(f"Error checking interactability: {str(e)}")
            return True  # Assume interactable on error

    async def _scroll_into_view(self, element: Any) -> None:
        """Scroll element into view."""
        try:
            script = """
            arguments[0].scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
            """
            await self.page.evaluate(script, element)
            await asyncio.sleep(0.3)  # Wait for scroll animation
        except Exception as e:
            logger.debug(f"Scroll into view failed: {str(e)}")

    async def _execute_click_strategy(
        self, element: Any, strategy: ClickStrategy
    ) -> bool:
        """Execute a specific click strategy."""
        if strategy == ClickStrategy.NORMAL:
            return await self._click_normal(element)
        elif strategy == ClickStrategy.JAVASCRIPT:
            return await self._click_javascript(element)
        elif strategy == ClickStrategy.FOCUS_ENTER:
            return await self._click_focus_enter(element)
        elif strategy == ClickStrategy.FOCUS_SPACE:
            return await self._click_focus_space(element)
        elif strategy == ClickStrategy.DISPATCH_EVENT:
            return await self._click_dispatch_event(element)
        elif strategy == ClickStrategy.DOUBLE_CLICK:
            return await self._click_double_click(element)

        return False

    async def _click_normal(self, element: Any) -> bool:
        """Standard element click."""
        try:
            await element.click()
            return True
        except Exception as e:
            logger.debug(f"Normal click failed: {str(e)}")
            return False

    async def _click_javascript(self, element: Any) -> bool:
        """Click using JavaScript."""
        try:
            script = "arguments[0].click();"
            await self.page.evaluate(script, element)
            return True
        except Exception as e:
            logger.debug(f"JavaScript click failed: {str(e)}")
            return False

    async def _click_focus_enter(self, element: Any) -> bool:
        """Focus element and press Enter."""
        try:
            await self._focus_element(element)
            await self._add_delay(50, 150)
            await self.page.send(
                uc.cdp.input_.dispatch_key_event(
                    type_='keyDown',
                    key='Enter',
                    code='Enter',
                    windows_virtual_key_code=13,
                    native_virtual_key_code=13
                )
            )
            await self._add_delay(10, 30)
            await self.page.send(
                uc.cdp.input_.dispatch_key_event(
                    type_='keyUp',
                    key='Enter',
                    code='Enter',
                    windows_virtual_key_code=13,
                    native_virtual_key_code=13
                )
            )
            return True
        except Exception as e:
            logger.debug(f"Focus+Enter click failed: {str(e)}")
            return False

    async def _click_focus_space(self, element: Any) -> bool:
        """Focus element and press Space."""
        try:
            await self._focus_element(element)
            await self._add_delay(50, 150)
            await self.page.send(
                uc.cdp.input_.dispatch_key_event(type_='keyDown', key=' ', code='Space')
            )
            await self._add_delay(10, 30)
            await self.page.send(
                uc.cdp.input_.dispatch_key_event(type_='keyUp', key=' ', code='Space')
            )
            return True
        except Exception as e:
            logger.debug(f"Focus+Space click failed: {str(e)}")
            return False

    async def _click_dispatch_event(self, element: Any) -> bool:
        """Dispatch click and mousedown/mouseup events."""
        try:
            script = """
            const el = arguments[0];
            el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """
            await self.page.evaluate(script, element)
            return True
        except Exception as e:
            logger.debug(f"Dispatch event click failed: {str(e)}")
            return False

    async def _click_double_click(self, element: Any) -> bool:
        """Double-click the element."""
        try:
            await element.click()
            await self._add_delay(10, 50)
            await element.click()
            return True
        except Exception as e:
            logger.debug(f"Double-click failed: {str(e)}")
            return False

    async def _focus_element(self, element: Any) -> None:
        """Focus an element."""
        script = "arguments[0].focus();"
        await self.page.evaluate(script, element)

    async def _verify_action(self, verify_func: Callable, timeout: float) -> bool:
        """Verify that click action had desired effect."""
        try:
            result = await asyncio.wait_for(verify_func(), timeout=timeout)
            return bool(result)
        except Exception as e:
            logger.debug(f"Verification failed: {str(e)}")
            return False

    async def _add_delay(self, min_ms: int, max_ms: int) -> None:
        """Add human-like random delay."""
        if self.human_like_delay:
            delay = random.randint(min_ms, max_ms) / 1000
            await asyncio.sleep(delay)


# Convenience function for direct use
async def smart_click(
    page,
    selector: str,
    verify_action: Optional[Callable] = None,
    timeout: float = 10.0,
) -> ClickResult:
    """
    Convenience function to click with smart strategies.

    Args:
        page: nodriver page object
        selector: CSS selector for element
        verify_action: Optional verification function
        timeout: Operation timeout

    Returns:
        ClickResult with success status
    """
    clicker = SmartClicker(page, verify_click=True, human_like_delay=True)
    return await clicker.click(selector, verify_action, timeout)
