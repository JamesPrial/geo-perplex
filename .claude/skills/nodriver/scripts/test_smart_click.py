#!/usr/bin/env python3
"""
Test suite for SmartClicker module.

Tests various click scenarios and strategies to ensure reliability.
Run against your target page to validate SmartClicker functionality.
"""

import asyncio
from typing import Optional
from smart_click import SmartClicker, ClickResult, ClickStrategy


class SmartClickTester:
    """Test runner for SmartClicker functionality."""

    def __init__(self, tab):
        """Initialize test runner."""
        self.tab = tab
        self.clicker = SmartClicker(tab)
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    async def run_all_tests(self):
        """Run all available tests."""
        print("\n" + "=" * 60)
        print("SmartClicker Test Suite")
        print("=" * 60)

        await self.test_element_found()
        await self.test_element_visible()
        await self.test_element_interactable()
        await self.test_normal_click()
        await self.test_javascript_click()
        await self.test_keyboard_click()
        await self.test_click_verification()
        await self.test_scroll_into_view()
        await self.test_multiple_strategies()
        await self.test_timeout_handling()

        self.print_summary()

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "PASS"
            symbol = "✓"
        else:
            status = "FAIL"
            symbol = "✗"

        print(f"{symbol} {name}: {status}")
        if details:
            print(f"  {details}")

        self.results.append({"name": name, "passed": passed, "details": details})

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Tests Run:  {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")

        if self.tests_passed == self.tests_run:
            print("\nAll tests passed! SmartClicker is working correctly.")
        else:
            print(f"\n{self.tests_run - self.tests_passed} tests failed.")
            print("\nFailed tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['details']}")

    async def test_element_found(self):
        """Test that elements can be found."""
        try:
            # This test assumes button exists on page
            elements = await self.tab.select_all("button")
            passed = len(elements) > 0
            self.log_test(
                "Element Found",
                passed,
                f"Found {len(elements)} button(s)"
            )
        except Exception as e:
            self.log_test("Element Found", False, str(e))

    async def test_element_visible(self):
        """Test visibility checking."""
        try:
            result = await self.clicker._check_element_visible(
                await self.tab.select("button")
            )
            self.log_test(
                "Element Visibility Check",
                isinstance(result, bool),
                f"Visibility: {result}"
            )
        except Exception as e:
            self.log_test("Element Visibility Check", False, str(e))

    async def test_element_interactable(self):
        """Test interactability checking."""
        try:
            button = await self.tab.select("button")
            result = await self.clicker._check_element_interactable(button)
            self.log_test(
                "Element Interactability Check",
                isinstance(result, bool),
                f"Interactable: {result}"
            )
        except Exception as e:
            self.log_test("Element Interactability Check", False, str(e))

    async def test_normal_click(self):
        """Test normal click strategy."""
        try:
            button = await self.tab.select("button")
            if not button:
                self.log_test("Normal Click Strategy", False,
                              "No button found")
                return

            success = await self.clicker._click_normal(button)
            self.log_test(
                "Normal Click Strategy",
                success,
                "Standard mouse click"
            )
        except Exception as e:
            self.log_test("Normal Click Strategy", False, str(e))

    async def test_javascript_click(self):
        """Test JavaScript click strategy."""
        try:
            button = await self.tab.select("button")
            if not button:
                self.log_test("JavaScript Click Strategy", False,
                              "No button found")
                return

            success = await self.clicker._click_javascript(button)
            self.log_test(
                "JavaScript Click Strategy",
                success,
                "element.click()"
            )
        except Exception as e:
            self.log_test("JavaScript Click Strategy", False, str(e))

    async def test_keyboard_click(self):
        """Test keyboard click strategies."""
        try:
            button = await self.tab.select("button")
            if not button:
                self.log_test("Keyboard Click Strategy", False,
                              "No button found")
                return

            # Test Focus+Enter
            success_enter = await self.clicker._click_focus_enter(button)

            # Test Focus+Space
            success_space = await self.clicker._click_focus_space(button)

            passed = success_enter or success_space
            self.log_test(
                "Keyboard Click Strategy",
                passed,
                f"Enter: {success_enter}, Space: {success_space}"
            )
        except Exception as e:
            self.log_test("Keyboard Click Strategy", False, str(e))

    async def test_click_verification(self):
        """Test click verification functionality."""
        try:
            call_count = 0

            async def verify_function():
                nonlocal call_count
                call_count += 1
                return True

            # Test verification is called
            result = await self.clicker.click(
                "button",
                verify_action=verify_function
            )

            verification_called = call_count > 0
            self.log_test(
                "Click Verification",
                verification_called and result.success,
                f"Verify called: {call_count} times"
            )
        except Exception as e:
            self.log_test("Click Verification", False, str(e))

    async def test_scroll_into_view(self):
        """Test scroll-into-view functionality."""
        try:
            button = await self.tab.select("button")
            if not button:
                self.log_test("Scroll Into View", False, "No button found")
                return

            await self.clicker._scroll_into_view(button)
            self.log_test(
                "Scroll Into View",
                True,
                "Successfully scrolled element into view"
            )
        except Exception as e:
            self.log_test("Scroll Into View", False, str(e))

    async def test_multiple_strategies(self):
        """Test that multiple strategies can be tried."""
        try:
            # Create a clicker with small max_retries to test strategy loop
            result = await self.clicker.click("button", timeout=5.0)

            strategies_tried = result.attempts > 0
            self.log_test(
                "Multiple Strategies",
                result.success,
                f"Strategies tried: {result.attempts}, "
                f"Used: {result.strategy_used.value}"
            )
        except Exception as e:
            self.log_test("Multiple Strategies", False, str(e))

    async def test_timeout_handling(self):
        """Test timeout handling."""
        try:
            # Try to click non-existent element with short timeout
            result = await self.clicker.click(
                "#nonexistent-element-xyz-12345",
                timeout=1.0
            )

            timeout_handled = not result.success
            self.log_test(
                "Timeout Handling",
                timeout_handled,
                f"Handled gracefully: {result.error}"
            )
        except asyncio.TimeoutError:
            # This is also acceptable
            self.log_test("Timeout Handling", True,
                          "Timeout exception raised appropriately")
        except Exception as e:
            self.log_test("Timeout Handling", False, str(e))


async def test_basic_scenarios(tab):
    """Test basic click scenarios."""
    print("\nBasic Scenario Tests")
    print("-" * 60)

    clicker = SmartClicker(tab)

    # Test 1: Find element
    buttons = await tab.select_all("button")
    print(f"Found {len(buttons)} buttons")

    # Test 2: Click first button
    if buttons:
        result = await clicker.click("button:first-of-type", timeout=5.0)
        print(f"Click result: {result.success}")
        print(f"Strategy used: {result.strategy_used.value}")
        print(f"Attempts: {result.attempts}")

    # Test 3: Click with verification
    verify_called = False

    async def verify_dummy():
        nonlocal verify_called
        verify_called = True
        return True

    if buttons:
        result = await clicker.click(
            "button:first-of-type",
            verify_action=verify_dummy
        )
        print(f"Verification called: {verify_called}")


async def test_different_selectors(tab):
    """Test clicking with different selectors."""
    print("\nDifferent Selector Tests")
    print("-" * 60)

    clicker = SmartClicker(tab)

    selectors = [
        ("button", "Type selector"),
        ("button:first-of-type", "Pseudo-selector"),
        ("[type='button']", "Attribute selector"),
        ("button[class]", "Compound selector"),
    ]

    for selector, description in selectors:
        try:
            result = await clicker.click(selector, timeout=3.0)
            status = "✓" if result.success else "✗"
            print(f"{status} {description}: {selector}")
        except Exception as e:
            print(f"✗ {description}: {selector} - {str(e)}")


async def test_strategy_preferences(tab):
    """Test different SmartClicker configurations."""
    print("\nConfiguration Tests")
    print("-" * 60)

    configs = [
        {
            "name": "Standard (all features)",
            "verify_click": True,
            "scroll_into_view": True,
            "human_like_delay": True,
        },
        {
            "name": "Fast (no verification)",
            "verify_click": False,
            "scroll_into_view": True,
            "human_like_delay": False,
        },
        {
            "name": "Thorough (all strategies)",
            "verify_click": True,
            "scroll_into_view": True,
            "human_like_delay": True,
            "max_retries": 6,
        },
    ]

    for config in configs:
        name = config.pop("name")
        clicker = SmartClicker(tab, **config)

        try:
            result = await clicker.click("button", timeout=3.0)
            strategy = result.strategy_used.value if result.success else "failed"
            print(f"✓ {name}: {strategy}")
        except Exception as e:
            print(f"✗ {name}: {str(e)}")


async def main():
    """Main test runner."""
    print("SmartClicker Test Suite - Standalone Mode")
    print("\nThis test script requires an active nodriver tab.")
    print("Usage example:")
    print("""
    import nodriver as uc
    from test_smart_click import main, SmartClickTester

    async def run():
        browser = await uc.start()
        tab = browser.main_tab
        await tab.open("https://example.com")

        tester = SmartClickTester(tab)
        await tester.run_all_tests()

    asyncio.run(run())
    """)


if __name__ == "__main__":
    asyncio.run(main())
