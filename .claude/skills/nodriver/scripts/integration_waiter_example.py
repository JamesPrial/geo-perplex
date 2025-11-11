#!/usr/bin/env python3
"""
Integration example showing ElementWaiter with SmartClicker and SafeTyper.

This demonstrates how to build a complete, robust browser automation workflow
by combining intelligent waiting, smart clicking, and safe typing.
"""

import asyncio
from dataclasses import dataclass
from element_waiter import (
    ElementWaiter,
    TextPresentCondition,
    JavaScriptCondition,
    wait_for_clickable,
    wait_for_text,
)


@dataclass
class LoginCredentials:
    """Login credentials."""

    email: str
    password: str


class RobustBrowserAutomation:
    """
    Complete automation workflow combining wait strategies, clicking, and typing.

    This class demonstrates best practices for reliable browser automation.
    """

    def __init__(self, tab, timeout: float = 10.0):
        """
        Initialize automation helper.

        Args:
            tab: nodriver tab object
            timeout: Default timeout for operations
        """
        self.tab = tab
        self.timeout = timeout
        self.waiter = ElementWaiter(tab, poll_interval=0.1)

    async def safe_click_and_wait(
        self,
        selector: str,
        wait_condition,
        timeout: float = None,
    ) -> bool:
        """
        Click element and wait for expected result.

        Args:
            selector: CSS selector for element to click
            wait_condition: WaitCondition to check after click
            timeout: Operation timeout

        Returns:
            True if click succeeded and condition was met
        """
        timeout = timeout or self.timeout

        try:
            # Step 1: Wait for element to be clickable
            result = await self.waiter.wait_for_clickable(
                selector, timeout=timeout
            )

            if not result.success:
                print(f"Element not clickable: {result.error}")
                return False

            # Step 2: Click the element
            print(f"Clicking {selector}...")
            await result.element.click()
            await asyncio.sleep(0.5)

            # Step 3: Wait for expected result
            print(f"Waiting for condition...")
            result = await self.waiter.wait_for_condition(
                wait_condition, None, timeout, None
            )

            if result.success:
                print(f"Condition met after click (waited {result.wait_time:.2f}s)")
                return True
            else:
                print(f"Condition not met: {result.error}")
                return False

        except Exception as e:
            print(f"Error during click and wait: {e}")
            return False

    async def safe_type_and_wait(
        self,
        selector: str,
        text: str,
        verify_text: bool = True,
        timeout: float = None,
    ) -> bool:
        """
        Type text into field and optionally verify.

        Args:
            selector: CSS selector for input field
            text: Text to type
            verify_text: Verify text was entered correctly
            timeout: Operation timeout

        Returns:
            True if typing succeeded
        """
        timeout = timeout or self.timeout

        try:
            # Step 1: Wait for field to be visible
            result = await self.waiter.wait_for_visible(
                selector, timeout=timeout
            )

            if not result.success:
                print(f"Field not visible: {result.error}")
                return False

            # Step 2: Click to focus
            element = result.element
            await element.click()
            await asyncio.sleep(0.2)

            # Step 3: Clear existing text
            await element.evaluate("arguments[0].value = '';", element)
            await asyncio.sleep(0.1)

            # Step 4: Type the text
            print(f"Typing into {selector}...")
            for char in text:
                await element.type(char)
                await asyncio.sleep(0.02)

            # Step 5: Verify if requested
            if verify_text:
                # Wait for value to match
                condition = JavaScriptCondition(
                    f"return document.querySelector('{selector}').value === '{text}';"
                )
                result = await self.waiter.wait_for_custom(
                    condition, timeout=timeout
                )

                if result.success:
                    print(f"Text verified: {text}")
                    return True
                else:
                    print(f"Text verification failed")
                    return False
            else:
                print(f"Text entered: {text}")
                return True

        except Exception as e:
            print(f"Error during typing: {e}")
            return False

    async def login_workflow(
        self, credentials: LoginCredentials, timeout: float = None
    ) -> bool:
        """
        Complete login workflow with robust error handling.

        Args:
            credentials: LoginCredentials with email and password
            timeout: Operation timeout

        Returns:
            True if login succeeded
        """
        timeout = timeout or self.timeout
        print("\nStarting login workflow...")
        print("=" * 50)

        try:
            # Step 1: Wait for login form
            print("\n[1] Waiting for login form...")
            result = await self.waiter.wait_for_visible(
                "#login-form", timeout=timeout
            )

            if not result.success:
                print(f"Login form not found: {result.error}")
                return False

            print(f"Login form found (waited {result.wait_time:.2f}s)")

            # Step 2: Enter email
            print("\n[2] Entering email...")
            success = await self.safe_type_and_wait(
                "#email-input", credentials.email, verify_text=True, timeout=timeout
            )
            if not success:
                return False

            # Step 3: Enter password
            print("\n[3] Entering password...")
            success = await self.safe_type_and_wait(
                "#password-input",
                credentials.password,
                verify_text=False,  # Don't verify passwords in output
                timeout=timeout,
            )
            if not success:
                return False

            # Step 4: Click login button and wait for result
            print("\n[4] Clicking login button...")
            result_condition = TextPresentCondition(
                "#message", "Login successful", partial=True
            )

            success = await self.safe_click_and_wait(
                "#login-btn", result_condition, timeout=timeout
            )

            if success:
                print("\n[5] Login successful!")
                return True
            else:
                # Check for error message
                error_condition = TextPresentCondition(
                    "#message", "Error", partial=True
                )
                result = await self.waiter.wait_for_custom(
                    error_condition, timeout=2
                )

                if result.success:
                    print("\n[5] Login failed - error message shown")
                else:
                    print("\n[5] Login - status unknown")

                return False

        except Exception as e:
            print(f"Login workflow error: {e}")
            return False

    async def fill_form_and_submit(
        self, form_data: dict, timeout: float = None
    ) -> bool:
        """
        Fill a multi-field form and submit.

        Args:
            form_data: Dict of {selector: value} pairs
            timeout: Operation timeout

        Returns:
            True if form submitted successfully
        """
        timeout = timeout or self.timeout
        print("\nFilling form...")
        print("=" * 50)

        try:
            # Fill each field
            for selector, value in form_data.items():
                print(f"\nFilling {selector}...")
                success = await self.safe_type_and_wait(
                    selector, value, verify_text=True, timeout=timeout
                )
                if not success:
                    print(f"Failed to fill {selector}")
                    return False

            # Submit form
            print("\nSubmitting form...")
            success_condition = TextPresentCondition(
                "#success-message", "submitted", partial=True
            )

            success = await self.safe_click_and_wait(
                "#submit-btn", success_condition, timeout=timeout
            )

            return success

        except Exception as e:
            print(f"Form submission error: {e}")
            return False

    async def wait_for_dynamic_content(
        self, selector: str, min_items: int = 1, timeout: float = None
    ) -> bool:
        """
        Wait for dynamic content to load.

        Args:
            selector: CSS selector for items
            min_items: Minimum number of items expected
            timeout: Operation timeout

        Returns:
            True if items loaded
        """
        timeout = timeout or self.timeout

        async def check_items_loaded(tab):
            """Check if minimum items are present and visible."""
            try:
                elements = await tab.select_all(selector)
                if len(elements) < min_items:
                    return False

                # Check if items are visible
                script = f"""
                const items = document.querySelectorAll('{selector}');
                return Array.from(items).slice(0, {min_items}).every(el => {{
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' && rect.height > 0;
                }});
                """
                return await tab.evaluate(script)
            except Exception:
                return False

        print(f"\nWaiting for {min_items}+ items matching {selector}...")
        result = await self.waiter.wait_for_custom(
            check_items_loaded, timeout=timeout
        )

        if result.success:
            print(f"Items loaded (waited {result.wait_time:.2f}s)")
            return True
        else:
            print(f"Items not loaded: {result.error}")
            return False


async def example_login():
    """
    Example: Login workflow.

    Demonstrates waiting for form, typing credentials, and verifying login.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Login Workflow with Robust Waits")
    print("=" * 70)

    code = """
    # Setup
    automation = RobustBrowserAutomation(tab, timeout=10)
    credentials = LoginCredentials(
        email="user@example.com",
        password="password123"
    )

    # Execute login
    success = await automation.login_workflow(credentials)

    if success:
        print("Successfully logged in!")
    else:
        print("Login failed")
    """
    print(code)


async def example_form():
    """
    Example: Multi-field form.

    Demonstrates filling and submitting a form with verification.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Multi-Field Form Submission")
    print("=" * 70)

    code = """
    automation = RobustBrowserAutomation(tab, timeout=10)

    form_data = {
        "#first-name": "John",
        "#last-name": "Doe",
        "#email": "john@example.com",
        "#phone": "555-0123",
        "#address": "123 Main St"
    }

    success = await automation.fill_form_and_submit(form_data)

    if success:
        print("Form submitted successfully!")
    else:
        print("Form submission failed")
    """
    print(code)


async def example_dynamic_content():
    """
    Example: Wait for dynamic content.

    Demonstrates waiting for list items to load and become visible.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Dynamic Content Loading")
    print("=" * 70)

    code = """
    automation = RobustBrowserAutomation(tab, timeout=30)

    # Wait for at least 10 items to load
    success = await automation.wait_for_dynamic_content(
        selector=".product-item",
        min_items=10,
        timeout=30
    )

    if success:
        print("Product list loaded")
        # Safe to interact with items now
    else:
        print("Failed to load products")
    """
    print(code)


async def example_combined():
    """
    Example: Combined workflow with multiple operations.

    Demonstrates a realistic scenario with login, navigation, and form submission.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Combined Workflow (Login -> Navigate -> Submit)")
    print("=" * 70)

    code = """
    async def complete_workflow(tab):
        automation = RobustBrowserAutomation(tab, timeout=10)

        # Step 1: Login
        login_ok = await automation.login_workflow(
            LoginCredentials("user@example.com", "pass123")
        )
        if not login_ok:
            return False

        # Step 2: Navigate to form
        form_result = await automation.waiter.wait_for_visible(
            "#contact-form", timeout=10
        )
        if not form_result.success:
            return False

        # Step 3: Fill and submit form
        success = await automation.fill_form_and_submit({
            "#name": "John Doe",
            "#message": "Hello, this is a test message",
        })

        return success

    # Execute workflow
    result = await complete_workflow(tab)
    print(f"Workflow result: {result}")
    """
    print(code)


async def main():
    """Run all integration examples."""
    print("\n" + "=" * 70)
    print("ElementWaiter Integration Examples")
    print("=" * 70)

    await example_login()
    await example_form()
    await example_dynamic_content()
    await example_combined()

    print("\n" + "=" * 70)
    print("Integration Examples Complete")
    print("=" * 70)
    print("\nKey takeaways:")
    print("1. Always wait for elements before interacting")
    print("2. Use specific conditions (visibility, clickability)")
    print("3. Handle failures gracefully with error checking")
    print("4. Verify operations succeeded before proceeding")
    print("5. Combine waits to create robust workflows\n")


if __name__ == "__main__":
    asyncio.run(main())
