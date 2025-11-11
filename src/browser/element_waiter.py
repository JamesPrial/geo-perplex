"""
Intelligent wait strategies for reliable element interaction with nodriver.

This module provides advanced waiting mechanisms that go beyond simple timeouts,
enabling robust browser automation by waiting for specific conditions to be met.

Features:
- Wait for element presence, visibility, and clickability
- Wait for text content in elements
- Wait for content stability (stops changing)
- Polling-based checks with configurable intervals
- Detailed result information for debugging

Example:
    >>> from src.browser.element_waiter import ElementWaiter
    >>> waiter = ElementWaiter(page)
    >>> result = await waiter.wait_for_clickable('#submit-btn', timeout=10)
    >>> if result.success:
    ...     await result.element.click()
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class WaitCondition(Enum):
    """Types of wait conditions supported by ElementWaiter."""
    PRESENCE = "presence"      # Element exists in DOM
    VISIBILITY = "visibility"  # Element is visible in viewport
    CLICKABILITY = "clickability"  # Element is clickable (visible, enabled, interactable)
    TEXT_PRESENT = "text_present"  # Element contains specific text
    TEXT_EQUALS = "text_equals"    # Element text exactly matches
    STABILITY = "stability"    # Element content stops changing


@dataclass
class WaitResult:
    """
    Result of a wait operation with detailed information.

    Attributes:
        success: Whether the condition was met
        element: The element found (if applicable)
        wait_time: Time spent waiting in seconds
        attempts: Number of polling attempts made
        condition_met: The condition that was satisfied
        error: Error message if unsuccessful
    """
    success: bool
    element: Optional[Any] = None
    wait_time: float = 0.0
    attempts: int = 0
    condition_met: Optional[WaitCondition] = None
    error: Optional[str] = None


class ElementWaiter:
    """
    Advanced wait strategies for element interactions in nodriver.

    This class provides intelligent waiting that checks for specific conditions
    before proceeding, making automation more reliable.

    Example:
        waiter = ElementWaiter(page)
        result = await waiter.wait_for_clickable('#button', timeout=10)
        if result.success:
            await result.element.click()
    """

    def __init__(
        self,
        page: Any,
        poll_interval: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize ElementWaiter.

        Args:
            page: The nodriver page object
            poll_interval: Time between condition checks in seconds (default: 0.1)
            verbose: Enable detailed logging (default: False)
        """
        self.page = page
        self.poll_interval = poll_interval
        self.verbose = verbose

        # Store common JavaScript checks for reuse
        self._visibility_script = """
        function isVisible(el) {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' ||
                style.opacity === '0') {
                return false;
            }
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 &&
                   rect.top < window.innerHeight && rect.left < window.innerWidth;
        }
        return isVisible(arguments[0]);
        """

        self._clickable_script = """
        function isClickable(el) {
            if (!el) return false;

            // Check visibility
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') {
                return false;
            }

            // Check disabled state
            if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
                return false;
            }

            // Check pointer-events
            if (style.pointerEvents === 'none') return false;

            // Check if in viewport
            const rect = el.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return false;
            if (rect.top >= window.innerHeight || rect.left >= window.innerWidth) {
                return false;
            }
            if (rect.bottom <= 0 || rect.right <= 0) return false;

            // Check if hidden by parent
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
        return isClickable(arguments[0]);
        """

    async def _wait_with_condition(
        self,
        selector: str,
        condition_check: Callable[[Any], Awaitable[bool]],
        condition_type: WaitCondition,
        timeout: float,
        error_prefix: str = ""
    ) -> WaitResult:
        """
        Generic wait implementation with customizable condition check.

        Args:
            selector: CSS selector for element
            condition_check: Async function that checks if condition is met
            condition_type: Type of condition being waited for
            timeout: Maximum wait time in seconds
            error_prefix: Prefix for error messages

        Returns:
            WaitResult with success status and element
        """
        start_time = time.time()
        attempts = 0

        if self.verbose:
            logger.debug(f"Waiting for {condition_type.value}: {selector} (timeout: {timeout}s)")

        try:
            while (time.time() - start_time) < timeout:
                attempts += 1

                try:
                    element = await self.page.select(selector, timeout=self.poll_interval)

                    if element:
                        # Check if condition is met
                        condition_met = await condition_check(element)

                        if condition_met:
                            elapsed = time.time() - start_time
                            if self.verbose:
                                logger.debug(
                                    f"{condition_type.value} condition met for {selector} "
                                    f"after {elapsed:.2f}s ({attempts} attempts)"
                                )

                            return WaitResult(
                                success=True,
                                element=element,
                                wait_time=elapsed,
                                attempts=attempts,
                                condition_met=condition_type,
                                error=None
                            )

                except Exception as e:
                    logger.debug(f"Error during wait attempt {attempts}: {str(e)}")

                # Wait before next attempt
                await asyncio.sleep(self.poll_interval)

            # Timeout reached
            elapsed = time.time() - start_time
            error_msg = f"{error_prefix}Timeout after {elapsed:.2f}s ({attempts} attempts)"

            if self.verbose:
                logger.warning(f"{condition_type.value} timeout: {selector} - {error_msg}")

            return WaitResult(
                success=False,
                element=None,
                wait_time=elapsed,
                attempts=attempts,
                condition_met=condition_type,
                error=error_msg
            )

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"{error_prefix}Error: {str(e)}"
            logger.error(f"Wait failed for {selector}: {error_msg}")

            return WaitResult(
                success=False,
                element=None,
                wait_time=elapsed,
                attempts=attempts,
                condition_met=condition_type,
                error=error_msg
            )

    async def _is_clickable(self, element: Any) -> bool:
        """Check if element is clickable using JavaScript."""
        try:
            is_clickable = await self.page.evaluate(self._clickable_script, element)
            return bool(is_clickable)
        except Exception:
            return False

    async def wait_for_presence(
        self,
        selector: str,
        timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to exist in DOM.

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element if found
        """

        async def check_presence(element) -> bool:
            """Element presence is already confirmed by select()."""
            return True

        return await self._wait_with_condition(
            selector=selector,
            condition_check=check_presence,
            condition_type=WaitCondition.PRESENCE,
            timeout=timeout,
            error_prefix="Element not present: "
        )

    async def wait_for_visibility(
        self,
        selector: str,
        timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to be visible in viewport.

        Checks that element:
        - Exists in DOM
        - Has display != 'none'
        - Has visibility != 'hidden'
        - Has opacity != '0'
        - Has non-zero dimensions

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element if visible
        """

        async def check_visibility(element) -> bool:
            """Check if element is visible using JavaScript."""
            try:
                is_visible = await self.page.evaluate(self._visibility_script, element)
                return bool(is_visible)
            except Exception:
                return False

        return await self._wait_with_condition(
            selector=selector,
            condition_check=check_visibility,
            condition_type=WaitCondition.VISIBILITY,
            timeout=timeout,
            error_prefix="Element not visible: "
        )

    async def wait_for_clickable(
        self,
        selector: str,
        timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to be clickable.

        Checks that element:
        - Exists in DOM
        - Is visible
        - Is not disabled
        - Has pointer-events enabled
        - Is in viewport
        - Is not covered by other elements

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element if clickable
        """

        async def check_clickable(element) -> bool:
            """Check if element is clickable."""
            return await self._is_clickable(element)

        return await self._wait_with_condition(
            selector=selector,
            condition_check=check_clickable,
            condition_type=WaitCondition.CLICKABILITY,
            timeout=timeout,
            error_prefix="Element not clickable: "
        )

    async def wait_for_text(
        self,
        selector: str,
        text: str,
        partial: bool = True,
        timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to contain specific text.

        Args:
            selector: CSS selector for element
            text: Text to wait for
            partial: If True, check for substring; if False, check exact match
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status
        """
        start_time = time.time()
        attempts = 0

        if self.verbose:
            match_type = "contains" if partial else "equals"
            logger.debug(f"Waiting for text ({match_type}): '{text}' in {selector}")

        try:
            while (time.time() - start_time) < timeout:
                attempts += 1

                try:
                    element = await self.page.select(selector, timeout=self.poll_interval)
                    if element:
                        # Get text content (text_all is a property, NOT async)
                        content = element.text_all
                        if content:
                            # Check text condition
                            if partial and text in content:
                                elapsed = time.time() - start_time
                                logger.debug(
                                    f"Text found (partial): '{text}' in {selector} "
                                    f"(after {elapsed:.2f}s)"
                                )
                                return WaitResult(
                                    success=True,
                                    element=element,
                                    wait_time=elapsed,
                                    attempts=attempts,
                                    condition_met=WaitCondition.TEXT_PRESENT
                                )
                            elif not partial and text == content.strip():
                                elapsed = time.time() - start_time
                                logger.debug(
                                    f"Text found (exact): '{text}' in {selector} "
                                    f"(after {elapsed:.2f}s)"
                                )
                                return WaitResult(
                                    success=True,
                                    element=element,
                                    wait_time=elapsed,
                                    attempts=attempts,
                                    condition_met=WaitCondition.TEXT_EQUALS
                                )
                except Exception:
                    pass

                await asyncio.sleep(self.poll_interval)

            # Timeout reached
            elapsed = time.time() - start_time
            match_type = "partial" if partial else "exact"
            logger.warning(
                f"Timeout waiting for text ({match_type}): '{text}' in {selector} "
                f"(after {elapsed:.2f}s)"
            )
            return WaitResult(
                success=False,
                wait_time=elapsed,
                attempts=attempts,
                error=f"Timeout after {elapsed:.2f}s"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error waiting for text: {e}")
            return WaitResult(
                success=False,
                wait_time=elapsed,
                attempts=attempts,
                error=str(e)
            )

    async def wait_for_stable(
        self,
        selector: str,
        timeout: float = 30.0,
        stable_threshold: int = 3,
        min_content_length: int = 50
    ) -> WaitResult:
        """
        Wait for element content to stop changing (stabilize).

        Uses MD5 hash-based change detection to determine when content
        has stopped being updated. Useful for waiting for dynamic content
        like AI-generated responses.

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds
            stable_threshold: Number of consecutive stable checks required
            min_content_length: Minimum content length to be considered valid

        Returns:
            WaitResult with success status and stabilized element
        """
        start_time = time.time()
        attempts = 0
        stable_count = 0
        last_hash = ""
        last_length = 0

        if self.verbose:
            logger.debug(f"Waiting for content stability: {selector}")

        try:
            while (time.time() - start_time) < timeout:
                attempts += 1

                try:
                    element = await self.page.select(selector, timeout=self.poll_interval)
                    if element:
                        # Get current content (text_all is a property, NOT async)
                        current_text = element.text_all
                        current_length = len(current_text) if current_text else 0

                        # Calculate hash for change detection
                        current_hash = (
                            hashlib.md5(current_text.encode()).hexdigest()
                            if current_text else ""
                        )

                        # Check if content meets minimum threshold and has stabilized
                        if current_length >= min_content_length:
                            if current_hash == last_hash and current_length == last_length:
                                stable_count += 1
                                if stable_count >= stable_threshold:
                                    elapsed = time.time() - start_time
                                    logger.info(
                                        f"Content stable: {selector} "
                                        f"({current_length} chars, after {elapsed:.2f}s)"
                                    )
                                    return WaitResult(
                                        success=True,
                                        element=element,
                                        wait_time=elapsed,
                                        attempts=attempts,
                                        condition_met=WaitCondition.STABILITY
                                    )
                            else:
                                # Content changed, reset counter
                                stable_count = 0
                                last_hash = current_hash
                                last_length = current_length
                                if self.verbose:
                                    logger.debug(f"Content changing: {current_length} chars")
                        else:
                            # Not enough content yet
                            stable_count = 0
                            last_hash = current_hash
                            last_length = current_length

                except Exception as e:
                    if self.verbose:
                        logger.debug(f"Stability check error: {e}")
                    pass

                await asyncio.sleep(self.poll_interval)

            # Timeout reached
            elapsed = time.time() - start_time
            logger.warning(
                f"Timeout waiting for stability: {selector} "
                f"(after {elapsed:.2f}s, last length: {last_length})"
            )
            return WaitResult(
                success=False,
                wait_time=elapsed,
                attempts=attempts,
                error=f"Timeout after {elapsed:.2f}s"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error waiting for stability: {e}")
            return WaitResult(
                success=False,
                wait_time=elapsed,
                attempts=attempts,
                error=str(e)
            )
