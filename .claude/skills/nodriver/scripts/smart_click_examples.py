#!/usr/bin/env python3
"""
Practical examples of using SmartClicker for common automation scenarios.

These examples show real-world patterns for reliable element interaction.
"""

import asyncio
from smart_click import SmartClicker, smart_click


# Example 1: Simple button click
async def example_simple_click(tab):
    """Click a button and check if it succeeded."""
    clicker = SmartClicker(tab)
    result = await clicker.click("#submit-button")

    if result.success:
        print(f"✓ Button clicked using {result.strategy_used.value}")
        return True
    else:
        print(f"✗ Click failed: {result.error}")
        return False


# Example 2: Click with verification
async def example_click_with_verification(tab):
    """Click a button and verify the action succeeded."""

    async def verify_form_submitted():
        """Check if success message appears."""
        success_msg = await tab.select(".success-message")
        return success_msg is not None

    clicker = SmartClicker(tab, verify_click=True)
    result = await clicker.click(
        "#form-submit",
        verify_action=verify_form_submitted,
        timeout=15.0,
    )

    if result.success and result.verification_passed:
        print("✓ Form submitted and verified")
        return True
    elif result.success:
        print("✓ Click succeeded but verification failed")
        return False
    else:
        print(f"✗ Click failed: {result.error}")
        return False


# Example 3: Click inside modal dialog
async def example_click_in_modal(tab):
    """Click button inside a modal dialog."""
    clicker = SmartClicker(
        tab,
        scroll_into_view=True,  # Modal may need scrolling
        verify_click=True,
    )

    # Modal dialogs often have overlay, but SmartClicker handles it
    result = await clicker.click("#modal-confirm-button")

    if result.success:
        print(f"✓ Modal button clicked (Strategy: {result.strategy_used.value})")
        await asyncio.sleep(0.5)  # Wait for modal animation
        return True
    else:
        print(f"✗ Modal button click failed: {result.error}")
        return False


# Example 4: Click in paginated list
async def example_paginate_and_click(tab):
    """Navigate through paginated results and click items."""
    clicker = SmartClicker(tab, human_like_delay=True)

    # Click through pages
    for page in range(1, 4):
        # Click page button
        result = await clicker.click(f"#page-{page}")
        if not result.success:
            print(f"✗ Failed to go to page {page}")
            return False

        print(f"✓ Navigated to page {page}")
        await asyncio.sleep(1)  # Wait for page load

        # Click first item on page
        item_result = await clicker.click(".item-link:first-child")
        if item_result.success:
            print(f"  ✓ Clicked item (used {item_result.strategy_used.value})")
            await asyncio.sleep(0.5)
        else:
            print(f"  ✗ Failed to click item")

    return True


# Example 5: Click with custom verification
async def example_click_verify_state_change(tab):
    """Click and verify that page state changed."""

    async def verify_expanded():
        """Check if section is expanded (aria-expanded)."""
        section = await tab.select("#collapsible-section")
        is_expanded = await tab.evaluate(
            "arguments[0].getAttribute('aria-expanded') === 'true'",
            section,
        )
        return is_expanded

    clicker = SmartClicker(tab, verify_click=True)
    result = await clicker.click(
        "#expand-button",
        verify_action=verify_expanded,
    )

    if result.verification_passed:
        print("✓ Section expanded and verified")
        return True
    else:
        print("✗ Section did not expand")
        return False


# Example 6: Click multiple elements in sequence
async def example_multi_click_sequence(tab):
    """Click multiple elements in a specific order."""
    clicker = SmartClicker(tab, human_like_delay=True)

    steps = [
        ("#step-1-btn", "Step 1"),
        ("#step-2-btn", "Step 2"),
        ("#step-3-btn", "Step 3"),
        ("#confirm-btn", "Confirm"),
    ]

    for selector, name in steps:
        result = await clicker.click(selector, timeout=10.0)

        if result.success:
            print(f"✓ {name}: {result.strategy_used.value}")
            await asyncio.sleep(0.5)  # Between-step delay
        else:
            print(f"✗ {name} failed: {result.error}")
            return False

    return True


# Example 7: Click with timeout handling
async def example_click_with_timeout(tab):
    """Handle timeout gracefully when element appears slowly."""
    clicker = SmartClicker(tab)

    try:
        result = await clicker.click(
            "#maybe-delayed-button",
            timeout=20.0,  # Longer timeout for slow pages
        )

        if result.success:
            print(f"✓ Button found and clicked")
            return True
        else:
            print(f"✗ Click failed: {result.error}")
            return False

    except asyncio.TimeoutError:
        print("✗ Operation timed out completely")
        return False


# Example 8: Resilient form submission
async def example_resilient_form(tab):
    """Fill form and submit with verification and retries."""
    clicker = SmartClicker(tab, verify_click=True, human_like_delay=True)

    # Fill form fields
    await tab.type_text("#email-input", "user@example.com")
    await asyncio.sleep(0.3)
    await tab.type_text("#password-input", "securePassword123")
    await asyncio.sleep(0.3)

    async def verify_submission():
        """Verify form was submitted successfully."""
        # Check for success page or message
        success_page = await tab.select(".success-page")
        success_msg = await tab.select(".success-message")
        return success_page is not None or success_msg is not None

    # Try to submit with verification
    result = await clicker.click(
        "#submit-button",
        verify_action=verify_submission,
        timeout=15.0,
    )

    if result.success:
        print(f"✓ Form submitted (Strategy: {result.strategy_used.value})")
        if result.verification_passed:
            print("  ✓ Submission verified")
            return True
        else:
            print("  ! Submission not verified yet")
            return False
    else:
        print(f"✗ Submission failed: {result.error}")
        return False


# Example 9: Click and navigate
async def example_click_and_navigate(tab):
    """Click element and wait for navigation."""
    clicker = SmartClicker(tab)

    # Get current URL
    original_url = await tab.evaluate("window.location.href")

    # Click navigation link
    result = await clicker.click("a#next-page-link")

    if result.success:
        print(f"✓ Clicked navigation link")

        # Wait for URL to change
        for attempt in range(10):  # Up to 5 seconds
            current_url = await tab.evaluate("window.location.href")
            if current_url != original_url:
                print(f"  ✓ Page navigated to {current_url}")
                return True
            await asyncio.sleep(0.5)

        print("  ! Navigation click succeeded but page didn't change")
        return False
    else:
        print(f"✗ Click failed: {result.error}")
        return False


# Example 10: Click with strategy selection preference
async def example_click_with_preferences(tab):
    """Configure SmartClicker based on page characteristics."""

    # For pages with heavy JavaScript event listeners
    clicker_js_heavy = SmartClicker(
        tab,
        verify_click=True,  # Verify because JS may not execute immediately
        scroll_into_view=True,
        human_like_delay=True,  # Avoid detection of automation
    )

    # For internal/stable pages without detection concerns
    clicker_internal = SmartClicker(
        tab,
        verify_click=False,  # Trust that click works
        scroll_into_view=False,  # Assume visible
        human_like_delay=False,  # Don't waste time on delays
    )

    # For pages with complex overlays/modals
    clicker_complex = SmartClicker(
        tab,
        verify_click=True,
        scroll_into_view=True,  # Definitely scroll into view
        human_like_delay=True,
        max_retries=6,  # Try more strategies
    )

    # Use appropriate clicker
    result = await clicker_js_heavy.click("#button")
    return result.success


# Example 11: Monitor strategy usage
async def example_monitor_strategies(tab):
    """Track which strategies work for different elements."""
    clicker = SmartClicker(tab)
    strategy_stats = {}

    buttons = await tab.select_all("button[data-clickable]")
    for i, button in enumerate(buttons):
        selector = f"button[data-clickable]:nth-of-type({i + 1})"
        result = await clicker.click(selector)

        if result.success:
            strategy_name = result.strategy_used.value
            strategy_stats[strategy_name] = strategy_stats.get(strategy_name, 0) + 1

    # Print statistics
    print("Strategy usage statistics:")
    for strategy, count in sorted(
        strategy_stats.items(), key=lambda x: -x[1]
    ):
        print(f"  {strategy}: {count} times")

    return True


# Example 12: Handle different element types
async def example_different_element_types(tab):
    """Click different element types with appropriate verification."""
    clicker = SmartClicker(tab, verify_click=True)

    # Button - verify click happened
    async def verify_button():
        return await tab.select(".result-shown")

    result = await clicker.click(
        "button#action",
        verify_action=verify_button,
    )
    print(f"Button: {result.success}")

    # Checkbox - verify checked state
    async def verify_checkbox():
        checkbox = await tab.select("input[type='checkbox']#agree")
        is_checked = await tab.evaluate("arguments[0].checked", checkbox)
        return is_checked

    result = await clicker.click(
        "input[type='checkbox']#agree",
        verify_action=verify_checkbox,
    )
    print(f"Checkbox: {result.verification_passed}")

    # Radio button - verify selected
    async def verify_radio():
        radio = await tab.select("input[type='radio'][name='option']")
        is_checked = await tab.evaluate("arguments[0].checked", radio)
        return is_checked

    result = await clicker.click(
        "input[type='radio'][name='option']:first-child",
        verify_action=verify_radio,
    )
    print(f"Radio: {result.verification_passed}")

    # Link - verify navigation (would check URL change)
    result = await clicker.click("a.external-link")
    print(f"Link: {result.success}")

    return True


# Example 13: Retry pattern with fallback
async def example_retry_with_fallback(tab):
    """Retry clicking with different selectors if element not found."""
    clicker = SmartClicker(tab)

    selectors = [
        "#primary-button",  # Try primary selector first
        "button.submit",  # Fallback to class-based selector
        "button[type='submit']",  # Fallback to attribute selector
        "[role='button'].submit",  # Fallback to role selector
    ]

    for selector in selectors:
        result = await clicker.click(selector, timeout=5.0)
        if result.success:
            print(f"✓ Found and clicked using: {selector}")
            return True
        else:
            print(f"✗ Not found: {selector}")

    print("✗ Could not find button with any selector")
    return False


# Example 14: Debug helper - log click details
async def example_debug_click_details(tab):
    """Log detailed information about click attempts."""
    clicker = SmartClicker(tab)

    result = await clicker.click("#target-button")

    print("Click Result Details:")
    print(f"  Success: {result.success}")
    print(f"  Strategy Used: {result.strategy_used.value}")
    print(f"  Attempts: {result.attempts}")
    if result.error:
        print(f"  Error: {result.error}")
    print(f"  Verification Passed: {result.verification_passed}")

    return result.success


async def main():
    """Show all examples."""
    print("SmartClicker - Practical Examples")
    print("=" * 50)
    print("\nThese examples show real-world usage patterns:")
    print("1. Simple button click")
    print("2. Click with verification")
    print("3. Click in modal dialog")
    print("4. Paginate and click")
    print("5. Verify state change")
    print("6. Multi-click sequence")
    print("7. Click with timeout")
    print("8. Resilient form submission")
    print("9. Click and navigate")
    print("10. Strategy preferences")
    print("11. Monitor strategy usage")
    print("12. Different element types")
    print("13. Retry with fallback")
    print("14. Debug click details")
    print("\nTo use these, import functions and call with your tab:")
    print("  result = await example_simple_click(my_tab)")


if __name__ == "__main__":
    asyncio.run(main())
