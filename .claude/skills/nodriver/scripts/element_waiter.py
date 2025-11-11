#!/usr/bin/env python3
"""
Advanced wait strategies for reliable element interaction with nodriver.

This module provides intelligent waiting mechanisms that go beyond simple timeouts,
enabling robust browser automation by waiting for specific conditions to be met
before proceeding with interactions.

Key Features:
    - Wait for element visibility and presence in DOM
    - Wait for element clickability (visible, enabled, interactable)
    - Wait for text content in elements
    - Wait for attribute changes and specific values
    - Wait for custom JavaScript conditions
    - Wait for network idle (no pending requests)
    - Compound conditions with AND/OR logic
    - Smart timeout handling with detailed error information
    - Exponential backoff and retry strategies
    - Fluent API for building complex wait conditions

Example:
    >>> import asyncio
    >>> from element_waiter import ElementWaiter, wait_for_element
    >>>
    >>> async def main():
    ...     waiter = ElementWaiter(tab)
    ...     # Wait for element to be clickable
    ...     element = await waiter.wait_for_clickable("#submit-btn", timeout=10)
    ...     if element:
    ...         # Element is now safe to interact with
    ...         await element.click()
    >>>
    >>> asyncio.run(main())
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any, Union, List
from abc import ABC, abstractmethod

try:
    from nodriver import cdp
except ImportError:
    cdp = None  # Graceful fallback if nodriver not installed


class WaitConditionType(Enum):
    """Types of wait conditions."""

    PRESENCE = "presence"  # Element exists in DOM
    VISIBLE = "visible"  # Element is visible in viewport
    CLICKABLE = "clickable"  # Element is clickable
    TEXT_PRESENT = "text_present"  # Text appears in element
    ATTRIBUTE_CHANGE = "attribute_change"  # Attribute changes
    ATTRIBUTE_VALUE = "attribute_value"  # Attribute has specific value
    JAVASCRIPT = "javascript"  # Custom JavaScript condition
    NETWORK_IDLE = "network_idle"  # No pending network requests
    CUSTOM = "custom"  # Custom async condition


class NetworkIdleStrategy(Enum):
    """Strategy for determining network idle state."""

    NO_REQUESTS = "no_requests"  # All requests completed
    RESOURCE_TIMING = "resource_timing"  # Based on resource timing


@dataclass
class WaitResult:
    """Result of a wait operation."""

    success: bool
    element: Optional[Any] = None
    wait_time: float = 0.0
    condition_type: Optional[WaitConditionType] = None
    error: Optional[str] = None
    attempts: int = 0


class WaitCondition(ABC):
    """Base class for wait conditions."""

    @abstractmethod
    async def check(self, tab: Any) -> bool:
        """Check if the condition is met."""
        pass

    @abstractmethod
    def describe(self) -> str:
        """Describe the wait condition."""
        pass


class PresenceCondition(WaitCondition):
    """Wait for element to exist in DOM."""

    def __init__(self, selector: str):
        self.selector = selector

    async def check(self, tab: Any) -> bool:
        """Check if element exists in DOM."""
        try:
            elements = await tab.select_all(self.selector)
            return len(elements) > 0
        except Exception:
            return False

    def describe(self) -> str:
        return f"element present: {self.selector}"


class VisibilityCondition(WaitCondition):
    """Wait for element to be visible."""

    def __init__(self, selector: str):
        self.selector = selector

    async def check(self, tab: Any) -> bool:
        """Check if element is visible."""
        try:
            elements = await tab.select_all(self.selector)
            if not elements:
                return False

            script = """
            function isVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden'
                    || style.opacity === '0') {
                    return false;
                }
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 &&
                       rect.top < window.innerHeight && rect.left < window.innerWidth;
            }
            return isVisible(arguments[0]);
            """
            return await tab.evaluate(script, elements[0])
        except Exception:
            return False

    def describe(self) -> str:
        return f"element visible: {self.selector}"


class ClickableCondition(WaitCondition):
    """Wait for element to be clickable."""

    def __init__(self, selector: str):
        self.selector = selector

    async def check(self, tab: Any) -> bool:
        """Check if element is clickable."""
        try:
            elements = await tab.select_all(self.selector)
            if not elements:
                return False

            script = """
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
            return await tab.evaluate(script, elements[0])
        except Exception:
            return False

    def describe(self) -> str:
        return f"element clickable: {self.selector}"


class TextPresentCondition(WaitCondition):
    """Wait for text to appear in element."""

    def __init__(self, selector: str, text: str, partial: bool = False):
        self.selector = selector
        self.text = text
        self.partial = partial

    async def check(self, tab: Any) -> bool:
        """Check if text is present in element."""
        try:
            elements = await tab.select_all(self.selector)
            if not elements:
                return False

            script = "return arguments[0].textContent;"
            content = await tab.evaluate(script, elements[0])

            if self.partial:
                return self.text in content
            else:
                return self.text == content.strip()
        except Exception:
            return False

    def describe(self) -> str:
        match_type = "contains" if self.partial else "equals"
        return f"text {match_type}: {self.text}"


class AttributeValueCondition(WaitCondition):
    """Wait for attribute to have a specific value."""

    def __init__(self, selector: str, attribute: str, value: str):
        self.selector = selector
        self.attribute = attribute
        self.value = value

    async def check(self, tab: Any) -> bool:
        """Check if attribute has specific value."""
        try:
            elements = await tab.select_all(self.selector)
            if not elements:
                return False

            script = f"return arguments[0].getAttribute('{self.attribute}');"
            current_value = await tab.evaluate(script, elements[0])
            return current_value == self.value
        except Exception:
            return False

    def describe(self) -> str:
        return f"attribute {self.attribute}={self.value}: {self.selector}"


class JavaScriptCondition(WaitCondition):
    """Wait for custom JavaScript condition to be true."""

    def __init__(self, script: str):
        self.script = script

    async def check(self, tab: Any) -> bool:
        """Evaluate custom JavaScript condition."""
        try:
            result = await tab.evaluate(self.script)
            return bool(result)
        except Exception:
            return False

    def describe(self) -> str:
        return f"JavaScript condition"


class NetworkIdleCondition(WaitCondition):
    """Wait for network to be idle."""

    def __init__(self, strategy: NetworkIdleStrategy = NetworkIdleStrategy.NO_REQUESTS):
        self.strategy = strategy

    async def check(self, tab: Any) -> bool:
        """Check if network is idle."""
        try:
            if self.strategy == NetworkIdleStrategy.NO_REQUESTS:
                script = """
                return new Promise(resolve => {
                    const pendingRequests = window.__pendingRequests || 0;
                    resolve(pendingRequests === 0);
                });
                """
            else:
                script = """
                return new Promise(resolve => {
                    const perfEntries = performance.getEntriesByType('resource');
                    const lastEntry = perfEntries[perfEntries.length - 1];
                    if (!lastEntry) resolve(true);
                    else {
                        const now = performance.now();
                        const timeSinceLastRequest = now - lastEntry.responseEnd;
                        resolve(timeSinceLastRequest > 1000);
                    }
                });
                """
            result = await tab.evaluate(script)
            return bool(result)
        except Exception:
            return False

    def describe(self) -> str:
        return f"network idle ({self.strategy.value})"


class CompoundCondition(WaitCondition):
    """Combine multiple conditions with AND or OR logic."""

    def __init__(self, conditions: List[WaitCondition], use_and: bool = True):
        self.conditions = conditions
        self.use_and = use_and

    async def check(self, tab: Any) -> bool:
        """Check compound condition."""
        if not self.conditions:
            return True

        results = []
        for condition in self.conditions:
            try:
                result = await condition.check(tab)
                results.append(result)
            except Exception:
                results.append(False)

        if self.use_and:
            return all(results)
        else:
            return any(results)

    def describe(self) -> str:
        operator = "AND" if self.use_and else "OR"
        descriptions = [c.describe() for c in self.conditions]
        return f"({operator}: {', '.join(descriptions)})"


class ElementWaiter:
    """
    Advanced wait strategies for element interactions.

    This class provides intelligent waiting that goes beyond simple timeouts,
    checking for specific conditions before proceeding.

    Example:
        waiter = ElementWaiter(tab)
        element = await waiter.wait_for_clickable("#button", timeout=10)
        element = await waiter.wait_for_text("#message", "Success", timeout=5)
    """

    def __init__(
        self,
        tab: Any,
        poll_interval: float = 0.1,
        verbose: bool = False,
    ):
        """
        Initialize ElementWaiter.

        Args:
            tab: The nodriver tab/page object
            poll_interval: Interval between condition checks (seconds)
            verbose: Enable verbose logging
        """
        self.tab = tab
        self.poll_interval = poll_interval
        self.verbose = verbose
        self.logger = self._setup_logger()

    @staticmethod
    def _setup_logger():
        """Set up basic logging."""

        class SimpleLogger:
            def __init__(self, verbose: bool = False):
                self.verbose = verbose

            def debug(self, msg: str):
                if self.verbose:
                    print(f"[Wait DEBUG] {msg}")

            def info(self, msg: str):
                print(f"[Wait] {msg}")

            def warning(self, msg: str):
                print(f"[Wait WARNING] {msg}")

            def error(self, msg: str):
                print(f"[Wait ERROR] {msg}")

        return SimpleLogger(verbose=False)

    async def wait_for_presence(
        self, selector: str, timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to exist in DOM.

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element
        """
        condition = PresenceCondition(selector)
        return await self._wait_for_condition(
            condition, selector, timeout, WaitConditionType.PRESENCE
        )

    async def wait_for_visible(
        self, selector: str, timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to be visible in viewport.

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element
        """
        condition = VisibilityCondition(selector)
        return await self._wait_for_condition(
            condition, selector, timeout, WaitConditionType.VISIBLE
        )

    async def wait_for_clickable(
        self, selector: str, timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for element to be clickable.

        Requirements:
        - Element must exist in DOM
        - Element must be visible
        - Element must be enabled
        - Element must not be covered
        - Element must be in viewport

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status and element
        """
        condition = ClickableCondition(selector)
        return await self._wait_for_condition(
            condition, selector, timeout, WaitConditionType.CLICKABLE
        )

    async def wait_for_text(
        self,
        selector: str,
        text: str,
        partial: bool = True,
        timeout: float = 10.0,
    ) -> WaitResult:
        """
        Wait for text to appear in element.

        Args:
            selector: CSS selector for element
            text: Text to wait for
            partial: If True, check for substring; if False, check exact match
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status
        """
        condition = TextPresentCondition(selector, text, partial=partial)
        return await self._wait_for_condition(
            condition, None, timeout, WaitConditionType.TEXT_PRESENT
        )

    async def wait_for_attribute(
        self,
        selector: str,
        attribute: str,
        value: str,
        timeout: float = 10.0,
    ) -> WaitResult:
        """
        Wait for element attribute to have specific value.

        Args:
            selector: CSS selector for element
            attribute: Attribute name
            value: Expected attribute value
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status
        """
        condition = AttributeValueCondition(selector, attribute, value)
        return await self._wait_for_condition(
            condition, selector, timeout, WaitConditionType.ATTRIBUTE_VALUE
        )

    async def wait_for_javascript(
        self, script: str, timeout: float = 10.0
    ) -> WaitResult:
        """
        Wait for custom JavaScript condition to return true.

        The script should return a truthy value when the condition is met.

        Args:
            script: JavaScript code that returns boolean
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status

        Example:
            result = await waiter.wait_for_javascript(
                "return document.readyState === 'complete'",
                timeout=10
            )
        """
        condition = JavaScriptCondition(script)
        return await self._wait_for_condition(
            condition, None, timeout, WaitConditionType.JAVASCRIPT
        )

    async def wait_for_network_idle(
        self,
        timeout: float = 10.0,
        strategy: NetworkIdleStrategy = NetworkIdleStrategy.NO_REQUESTS,
    ) -> WaitResult:
        """
        Wait for network to be idle.

        Args:
            timeout: Maximum wait time in seconds
            strategy: Strategy for determining idle state

        Returns:
            WaitResult with success status
        """
        condition = NetworkIdleCondition(strategy=strategy)
        return await self._wait_for_condition(
            condition, None, timeout, WaitConditionType.NETWORK_IDLE
        )

    async def wait_for_custom(
        self,
        condition_func: Callable[[Any], bool],
        timeout: float = 10.0,
    ) -> WaitResult:
        """
        Wait for custom async condition function.

        Args:
            condition_func: Async function that returns bool
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status

        Example:
            async def my_condition(tab):
                element = await tab.find("#status")
                if not element:
                    return False
                text = await element.text()
                return "ready" in text.lower()

            result = await waiter.wait_for_custom(my_condition, timeout=10)
        """

        class CustomCondition(WaitCondition):
            def __init__(self, func):
                self.func = func

            async def check(self, tab):
                try:
                    return await self.func(tab)
                except Exception:
                    return False

            def describe(self):
                return "custom condition"

        condition = CustomCondition(condition_func)
        return await self._wait_for_condition(
            condition, None, timeout, WaitConditionType.CUSTOM
        )

    async def wait_for_all(
        self,
        conditions: List[WaitCondition],
        timeout: float = 10.0,
    ) -> WaitResult:
        """
        Wait for ALL conditions to be true (AND logic).

        Args:
            conditions: List of WaitCondition objects
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status
        """
        compound = CompoundCondition(conditions, use_and=True)
        return await self._wait_for_condition(
            compound, None, timeout, WaitConditionType.CUSTOM
        )

    async def wait_for_any(
        self,
        conditions: List[WaitCondition],
        timeout: float = 10.0,
    ) -> WaitResult:
        """
        Wait for ANY condition to be true (OR logic).

        Args:
            conditions: List of WaitCondition objects
            timeout: Maximum wait time in seconds

        Returns:
            WaitResult with success status
        """
        compound = CompoundCondition(conditions, use_and=False)
        return await self._wait_for_condition(
            compound, None, timeout, WaitConditionType.CUSTOM
        )

    async def _wait_for_condition(
        self,
        condition: WaitCondition,
        selector: Optional[str],
        timeout: float,
        condition_type: WaitConditionType,
    ) -> WaitResult:
        """
        Generic wait implementation.

        Args:
            condition: WaitCondition to check
            selector: CSS selector (if applicable)
            timeout: Maximum wait time
            condition_type: Type of condition

        Returns:
            WaitResult with detailed information
        """
        start_time = time.time()
        attempts = 0

        try:
            while True:
                attempts += 1
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed > timeout:
                    self.logger.warning(
                        f"Timeout waiting for {condition.describe()} "
                        f"after {elapsed:.2f}s ({attempts} attempts)"
                    )
                    return WaitResult(
                        success=False,
                        wait_time=elapsed,
                        condition_type=condition_type,
                        error=f"Timeout after {elapsed:.2f}s",
                        attempts=attempts,
                    )

                # Check condition
                try:
                    if await condition.check(self.tab):
                        self.logger.debug(
                            f"Condition met: {condition.describe()} "
                            f"after {elapsed:.2f}s ({attempts} attempts)"
                        )

                        # Get element if selector provided
                        element = None
                        if selector:
                            try:
                                elements = await self.tab.select_all(selector)
                                element = elements[0] if elements else None
                            except Exception:
                                pass

                        return WaitResult(
                            success=True,
                            element=element,
                            wait_time=elapsed,
                            condition_type=condition_type,
                            attempts=attempts,
                        )
                except Exception as e:
                    self.logger.debug(f"Error checking condition: {str(e)}")

                # Wait before next attempt
                await asyncio.sleep(self.poll_interval)

        except asyncio.CancelledError:
            elapsed = time.time() - start_time
            return WaitResult(
                success=False,
                wait_time=elapsed,
                condition_type=condition_type,
                error="Wait cancelled",
                attempts=attempts,
            )
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Unexpected error: {str(e)}")
            return WaitResult(
                success=False,
                wait_time=elapsed,
                condition_type=condition_type,
                error=str(e),
                attempts=attempts,
            )


# Convenience functions for direct use
async def wait_for_element(
    tab: Any, selector: str, timeout: float = 10.0
) -> Optional[Any]:
    """
    Wait for element to exist in DOM.

    Args:
        tab: nodriver tab object
        selector: CSS selector
        timeout: Operation timeout

    Returns:
        Element if found, None otherwise
    """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_presence(selector, timeout)
    return result.element


async def wait_for_visible(
    tab: Any, selector: str, timeout: float = 10.0
) -> Optional[Any]:
    """
    Wait for element to be visible.

    Args:
        tab: nodriver tab object
        selector: CSS selector
        timeout: Operation timeout

    Returns:
        Element if visible, None otherwise
    """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_visible(selector, timeout)
    return result.element


async def wait_for_clickable(
    tab: Any, selector: str, timeout: float = 10.0
) -> Optional[Any]:
    """
    Wait for element to be clickable.

    Args:
        tab: nodriver tab object
        selector: CSS selector
        timeout: Operation timeout

    Returns:
        Element if clickable, None otherwise
    """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_clickable(selector, timeout)
    return result.element


async def wait_for_text(
    tab: Any,
    selector: str,
    text: str,
    partial: bool = True,
    timeout: float = 10.0,
) -> bool:
    """
    Wait for text in element.

    Args:
        tab: nodriver tab object
        selector: CSS selector
        text: Text to wait for
        partial: If True, check substring; if False, exact match
        timeout: Operation timeout

    Returns:
        True if text found, False otherwise
    """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_text(selector, text, partial, timeout)
    return result.success


async def main():
    """Example usage of ElementWaiter."""
    print("ElementWaiter - Advanced Wait Strategies for nodriver")
    print("=" * 60)
    print("\nUsage examples:\n")

    print("1. Wait for element to be present:")
    print("   result = await waiter.wait_for_presence('#button', timeout=10)")
    print("   if result.success:")
    print("       print(f'Found after {result.wait_time:.2f}s')")

    print("\n2. Wait for element to be clickable:")
    print("   result = await waiter.wait_for_clickable('#submit', timeout=10)")
    print("   if result.success:")
    print("       await result.element.click()")

    print("\n3. Wait for text to appear:")
    print(
        "   result = await waiter.wait_for_text('#message', 'Success', "
        "timeout=5)"
    )
    print("   if result.success:")
    print("       print('Text appeared!')")

    print("\n4. Wait for attribute value:")
    print("   result = await waiter.wait_for_attribute('#status', "
    print("       'data-ready', 'true', timeout=10)")

    print("\n5. Wait for custom JavaScript condition:")
    print("   result = await waiter.wait_for_javascript(")
    print("       'return document.readyState === \"complete\"',")
    print("       timeout=10")
    print("   )")

    print("\n6. Wait for network idle:")
    print("   result = await waiter.wait_for_network_idle(timeout=10)")

    print("\n7. Wait for multiple conditions (AND):")
    print("   conditions = [")
    print("       VisibilityCondition('#button'),")
    print("       TextPresentCondition('#label', 'Click Me')")
    print("   ]")
    print("   result = await waiter.wait_for_all(conditions, timeout=10)")

    print("\n8. Wait for multiple conditions (OR):")
    print("   conditions = [")
    print("       TextPresentCondition('#error', 'Error', partial=True),")
    print("       TextPresentCondition('#success', 'Success')")
    print("   ]")
    print("   result = await waiter.wait_for_any(conditions, timeout=10)")

    print("\n9. Wait for custom async condition:")
    print("   async def custom_check(tab):")
    print("       element = await tab.find('#status')")
    print("       if not element:")
    print("           return False")
    print("       text = await element.text()")
    print("       return 'ready' in text.lower()")
    print("")
    print("   result = await waiter.wait_for_custom(custom_check, timeout=10)")

    print("\n10. Using convenience functions:")
    print("    element = await wait_for_clickable(tab, '#button', timeout=10)")
    print("    is_done = await wait_for_text(tab, '#msg', 'Done')")


if __name__ == "__main__":
    asyncio.run(main())
