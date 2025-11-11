#!/usr/bin/env python3
"""
Usage examples and test cases for ElementWaiter.

This file demonstrates various wait strategies and patterns for reliable
element interaction in browser automation.
"""

import asyncio
from element_waiter import (
    ElementWaiter,
    VisibilityCondition,
    ClickableCondition,
    TextPresentCondition,
    AttributeValueCondition,
    JavaScriptCondition,
    CompoundCondition,
    wait_for_element,
    wait_for_visible,
    wait_for_clickable,
    wait_for_text,
)


async def example_1_basic_presence():
    """Example 1: Wait for element to be present in DOM."""
    print("\n[Example 1] Wait for element to be present")
    print("-" * 50)

    # This would work with real nodriver tab
    # waiter = ElementWaiter(tab)
    # result = await waiter.wait_for_presence("#login-form", timeout=10)
    # if result.success:
    #     print(f"Element found after {result.wait_time:.2f}s")
    # else:
    #     print(f"Failed: {result.error}")

    code = """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_presence("#login-form", timeout=10)
    if result.success:
        print(f"Element found after {result.wait_time:.2f}s")
    """
    print(code)


async def example_2_visibility():
    """Example 2: Wait for element to become visible."""
    print("\n[Example 2] Wait for element to become visible")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_visible("#success-message", timeout=5)

    if result.success:
        print(f"Element visible after {result.wait_time:.2f}s")
    else:
        print(f"Timeout: {result.error}")
    """
    print(code)


async def example_3_clickable():
    """Example 3: Wait for element to be clickable."""
    print("\n[Example 3] Wait for element to be clickable")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_clickable("#submit-btn", timeout=10)

    if result.success:
        # Element is now safe to interact with
        await result.element.click()
        print(f"Clicked after {result.wait_time:.2f}s")
    else:
        print(f"Element not clickable: {result.error}")
    """
    print(code)


async def example_4_text_content():
    """Example 4: Wait for text to appear in element."""
    print("\n[Example 4] Wait for text content")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)

    # Partial match (substring)
    result = await waiter.wait_for_text(
        "#status-message",
        "Success",
        partial=True,
        timeout=5
    )

    if result.success:
        print(f"Text appeared after {result.wait_time:.2f}s")

    # Exact match
    result = await waiter.wait_for_text(
        "#counter",
        "100",
        partial=False,
        timeout=10
    )
    """
    print(code)


async def example_5_attribute_value():
    """Example 5: Wait for attribute to have specific value."""
    print("\n[Example 5] Wait for attribute value change")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)

    # Wait for data-ready attribute to become "true"
    result = await waiter.wait_for_attribute(
        "#component",
        "data-ready",
        "true",
        timeout=10
    )

    if result.success:
        print(f"Attribute ready after {result.wait_time:.2f}s")

    # Wait for button to be enabled
    result = await waiter.wait_for_attribute(
        "#save-btn",
        "disabled",
        "",  # Empty string means attribute is removed
        timeout=5
    )
    """
    print(code)


async def example_6_javascript_condition():
    """Example 6: Wait for custom JavaScript condition."""
    print("\n[Example 6] Wait for JavaScript condition")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)

    # Wait for page to be fully loaded
    result = await waiter.wait_for_javascript(
        "return document.readyState === 'complete'",
        timeout=10
    )

    # Wait for specific data to be available
    result = await waiter.wait_for_javascript(
        '''
        const data = window.__appState;
        return data && data.isReady === true && data.items.length > 0;
        ''',
        timeout=10
    )

    # Wait for AJAX calls to complete
    result = await waiter.wait_for_javascript(
        "return !document.body.classList.contains('loading')",
        timeout=5
    )
    """
    print(code)


async def example_7_network_idle():
    """Example 7: Wait for network idle."""
    print("\n[Example 7] Wait for network idle")
    print("-" * 50)

    code = """
    from element_waiter import NetworkIdleStrategy

    waiter = ElementWaiter(tab)

    # Wait for all network requests to complete
    result = await waiter.wait_for_network_idle(
        timeout=10,
        strategy=NetworkIdleStrategy.NO_REQUESTS
    )

    if result.success:
        print("Network is now idle")
    """
    print(code)


async def example_8_compound_conditions():
    """Example 8: Wait for multiple conditions with AND/OR logic."""
    print("\n[Example 8] Compound wait conditions")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)

    # AND logic: All conditions must be true
    conditions = [
        VisibilityCondition("#button"),
        TextPresentCondition("#label", "Click Me"),
        AttributeValueCondition("#button", "data-enabled", "true")
    ]
    result = await waiter.wait_for_all(conditions, timeout=10)

    if result.success:
        print("All conditions met")

    # OR logic: At least one condition must be true
    conditions = [
        TextPresentCondition("#error", "Error", partial=True),
        TextPresentCondition("#success", "Success"),
        JavaScriptCondition("return window.__apiError !== undefined")
    ]
    result = await waiter.wait_for_any(conditions, timeout=10)

    if result.success:
        print("At least one condition met")
    """
    print(code)


async def example_9_custom_condition():
    """Example 9: Wait for custom async condition."""
    print("\n[Example 9] Custom async condition")
    print("-" * 50)

    code = """
    async def custom_check(tab):
        '''Check if element contains a specific pattern.'''
        try:
            elements = await tab.select_all(".data-row")
            if not elements:
                return False
            # Check if we have the expected number of rows
            return len(elements) >= 5
        except Exception:
            return False

    waiter = ElementWaiter(tab)
    result = await waiter.wait_for_custom(custom_check, timeout=10)

    if result.success:
        print("All data rows loaded")
    """
    print(code)


async def example_10_convenience_functions():
    """Example 10: Using convenience functions."""
    print("\n[Example 10] Convenience functions")
    print("-" * 50)

    code = """
    # Quick helpers that return element or boolean directly

    # Wait for and get element
    element = await wait_for_element(tab, "#button", timeout=10)
    if element:
        await element.click()

    # Wait for visibility
    element = await wait_for_visible(tab, "#modal", timeout=5)

    # Wait for clickability
    element = await wait_for_clickable(tab, "#submit", timeout=10)
    if element:
        await element.click()

    # Wait for text
    success = await wait_for_text(
        tab,
        "#message",
        "Processing complete",
        timeout=30
    )
    """
    print(code)


async def example_11_error_handling():
    """Example 11: Proper error handling."""
    print("\n[Example 11] Error handling patterns")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab, verbose=False)

    try:
        result = await waiter.wait_for_clickable("#submit", timeout=10)

        if not result.success:
            print(f"Failed: {result.error}")
            print(f"Attempts: {result.attempts}")
            print(f"Wait time: {result.wait_time:.2f}s")
            # Handle failure appropriately
            raise TimeoutError(f"Element not clickable: {result.error}")

        # Safe to interact now
        await result.element.click()

    except asyncio.TimeoutError:
        print("Operation timed out")
    except Exception as e:
        print(f"Error: {e}")
    """
    print(code)


async def example_12_complex_workflow():
    """Example 12: Complex multi-step workflow."""
    print("\n[Example 12] Complex workflow with multiple waits")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab)

    # Step 1: Wait for login form to be visible
    result = await waiter.wait_for_visible("#login-form", timeout=10)
    if not result.success:
        raise TimeoutError("Login form not found")

    # Step 2: Wait for email field to be ready
    result = await waiter.wait_for_clickable("#email-input", timeout=5)
    if result.success:
        await result.element.type("user@example.com")

    # Step 3: Wait for password field
    result = await waiter.wait_for_visible("#password-input", timeout=5)
    if result.success:
        await result.element.type("password123")

    # Step 4: Wait for submit button to be clickable
    result = await waiter.wait_for_clickable("#submit-btn", timeout=5)
    if result.success:
        await result.element.click()

    # Step 5: Wait for success message or redirect
    success_condition = TextPresentCondition(
        "#message",
        "Login successful",
        partial=True
    )
    redirect_condition = JavaScriptCondition(
        "return window.location.pathname === '/dashboard'"
    )

    result = await waiter.wait_for_any(
        [success_condition, redirect_condition],
        timeout=10
    )

    if result.success:
        print("Login completed successfully")
    """
    print(code)


async def example_13_performance_patterns():
    """Example 13: Performance optimization patterns."""
    print("\n[Example 13] Performance optimization patterns")
    print("-" * 50)

    code = """
    waiter = ElementWaiter(tab, poll_interval=0.05)  # 50ms polling

    # Use shorter timeouts for quick checks
    result = await waiter.wait_for_visible("#loading", timeout=0.5)
    if not result.success:
        # If loading doesn't appear quickly, assume page is ready
        print("Page appears to be ready")

    # Use longer timeouts for operations that take time
    result = await waiter.wait_for_text(
        "#upload-status",
        "Upload complete",
        timeout=60  # Long timeout for file upload
    )

    # Combine fast checks for quick failure
    conditions = [
        JavaScriptCondition("return document.readyState === 'complete'"),
        VisibilityCondition("#main-content")
    ]
    result = await waiter.wait_for_all(conditions, timeout=5)
    """
    print(code)


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ElementWaiter - Advanced Wait Strategies Examples")
    print("=" * 60)

    await example_1_basic_presence()
    await example_2_visibility()
    await example_3_clickable()
    await example_4_text_content()
    await example_5_attribute_value()
    await example_6_javascript_condition()
    await example_7_network_idle()
    await example_8_compound_conditions()
    await example_9_custom_condition()
    await example_10_convenience_functions()
    await example_11_error_handling()
    await example_12_complex_workflow()
    await example_13_performance_patterns()

    print("\n" + "=" * 60)
    print("For more details, see element_waiter.py docstrings")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
