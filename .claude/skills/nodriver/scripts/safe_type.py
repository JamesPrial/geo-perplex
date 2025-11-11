#!/usr/bin/env python3
"""
Reliable text input module for nodriver with multiple fallback strategies.

This module provides robust text input handling with workarounds for common
browser automation challenges, including the send_keys() truncation bug,
special character handling, and verification mechanisms.

Key Features:
    - Character-by-character typing with configurable delays
    - JavaScript-based text injection as fallback
    - Clipboard paste simulation for complex content
    - Input field clearing before typing
    - Special character and modifier key handling
    - Verification that text was entered correctly
    - Multiple retry strategies for reliability

Example:
    >>> import asyncio
    >>> from safe_type import SafeTyper
    >>> from quick_start import create_browser
    >>>
    >>> async def main():
    ...     browser = await create_browser()
    ...     try:
    ...         page = await browser.get("https://example.com")
    ...         typer = SafeTyper(page)
    ...         await typer.type_in_field("#email-input", "user@example.com")
    ...     finally:
    ...         await browser.aclose()
    >>>
    >>> asyncio.run(main())
"""

import asyncio
import base64
from dataclasses import dataclass
from typing import Optional, Union
from enum import Enum


class TypingStrategy(Enum):
    """Strategy selection for text input."""
    CHARACTER_BY_CHARACTER = "character"
    JAVASCRIPT_INJECT = "javascript"
    CLIPBOARD_PASTE = "clipboard"


class SpecialKeys(Enum):
    """Keyboard special keys for text input."""
    SHIFT = "Shift"
    CONTROL = "Control"
    ALT = "Alt"
    META = "Meta"
    BACKSPACE = "Backspace"
    DELETE = "Delete"
    ENTER = "Enter"
    TAB = "Tab"
    SPACE = " "


@dataclass
class TypeConfig:
    """
    Configuration options for text input behavior.

    Attributes:
        initial_delay: Delay before starting typing (seconds)
        char_delay: Delay between each character (seconds)
        key_down_delay: Delay for key down events (seconds)
        verify_after: Verify text after typing (default: True)
        retry_count: Number of retry attempts (default: 3)
        clear_first: Clear field before typing (default: True)
        strategy: Typing strategy to use (default: CHARACTER_BY_CHARACTER)
    """
    initial_delay: float = 0.1
    char_delay: float = 0.05
    key_down_delay: float = 0.02
    verify_after: bool = True
    retry_count: int = 3
    clear_first: bool = True
    strategy: TypingStrategy = TypingStrategy.CHARACTER_BY_CHARACTER


class SafeTyper:
    """
    Reliable text input handler for browser automation with nodriver.

    This class provides multiple strategies for typing text reliably,
    handling edge cases like special characters, long text, and
    problematic input fields.
    """

    def __init__(self, page, config: Optional[TypeConfig] = None):
        """
        Initialize SafeTyper instance.

        Args:
            page: nodriver page object
            config: TypeConfig instance or None for defaults
        """
        self.page = page
        self.config = config or TypeConfig()

    async def type_in_field(
        self,
        selector: str,
        text: str,
        strategy: Optional[TypingStrategy] = None,
    ) -> bool:
        """
        Type text into an input field using the selected strategy.

        This is the main entry point that handles strategy selection and
        fallback logic.

        Args:
            selector: CSS selector for the input field
            text: Text to type
            strategy: Override default strategy (default: None for config default)

        Returns:
            True if text was successfully entered, False otherwise

        Raises:
            TimeoutError: If element not found or interaction fails
        """
        strategy = strategy or self.config.strategy

        # Try primary strategy
        if strategy == TypingStrategy.CHARACTER_BY_CHARACTER:
            success = await self._type_character_by_character(selector, text)
        elif strategy == TypingStrategy.JAVASCRIPT_INJECT:
            success = await self._inject_via_javascript(selector, text)
        elif strategy == TypingStrategy.CLIPBOARD_PASTE:
            success = await self._paste_via_clipboard(selector, text)
        else:
            success = False

        # If primary strategy fails, try JavaScript injection as fallback
        if not success and strategy != TypingStrategy.JAVASCRIPT_INJECT:
            try:
                success = await self._inject_via_javascript(selector, text)
            except Exception:
                pass

        # Verify text was entered if enabled
        if success and self.config.verify_after:
            success = await self._verify_text(selector, text)

        return success

    async def _type_character_by_character(
        self,
        selector: str,
        text: str,
    ) -> bool:
        """
        Type text character-by-character with delays between keystrokes.

        This approach minimizes the risk of text truncation and handles
        dynamic input fields better than bulk send_keys().

        Args:
            selector: CSS selector for the input field
            text: Text to type

        Returns:
            True if typing completed successfully
        """
        try:
            # Clear field first if configured
            if self.config.clear_first:
                await self._clear_field(selector)

            # Get the element and focus it
            element = await self.page.find(selector)
            if not element:
                return False

            await element.focus()
            await asyncio.sleep(self.config.initial_delay)

            # Type each character with delay
            for char in text:
                # Handle special characters
                if char == "\n":
                    await element.press("Enter")
                elif char == "\t":
                    await element.press("Tab")
                else:
                    # Regular character
                    await element.type(char)

                # Small delay between characters
                await asyncio.sleep(self.config.char_delay)

            return True

        except Exception as e:
            print(f"Error during character-by-character typing: {e}")
            return False

    async def _clear_field(self, selector: str) -> bool:
        """
        Clear an input field by selecting all and deleting.

        Args:
            selector: CSS selector for the input field

        Returns:
            True if field was cleared successfully
        """
        try:
            element = await self.page.find(selector)
            if not element:
                return False

            await element.focus()
            await asyncio.sleep(0.05)

            # Select all and delete
            await element.press("Control+a")
            await asyncio.sleep(0.05)
            await element.press("Backspace")
            await asyncio.sleep(0.05)

            return True

        except Exception as e:
            print(f"Error clearing field: {e}")
            return False

    async def _inject_via_javascript(
        self,
        selector: str,
        text: str,
    ) -> bool:
        """
        Inject text directly via JavaScript as fallback.

        This bypasses the input field entirely and sets the value directly,
        which works for most cases but may not trigger all events.

        Args:
            selector: CSS selector for the input field
            text: Text to inject

        Returns:
            True if injection was successful
        """
        try:
            # Escape the text for JavaScript
            escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')

            # JavaScript to set value and trigger events
            js_code = f"""
            (function() {{
                const element = document.querySelector('{selector}');
                if (!element) return false;

                // Set the value
                element.value = "{escaped_text}";

                // Trigger input events
                const events = ['input', 'change', 'blur'];
                events.forEach(evt => {{
                    element.dispatchEvent(new Event(evt, {{ bubbles: true }}));
                }});

                return true;
            }})()
            """

            result = await self.page.evaluate(js_code)
            return result is True

        except Exception as e:
            print(f"Error injecting text via JavaScript: {e}")
            return False

    async def _paste_via_clipboard(
        self,
        selector: str,
        text: str,
    ) -> bool:
        """
        Paste text via clipboard simulation.

        This strategy encodes text in base64 and uses JavaScript to
        simulate a clipboard paste operation.

        Args:
            selector: CSS selector for the input field
            text: Text to paste

        Returns:
            True if paste was successful
        """
        try:
            # Clear field first
            if self.config.clear_first:
                await self._clear_field(selector)

            # Focus the element
            element = await self.page.find(selector)
            if not element:
                return False

            await element.focus()
            await asyncio.sleep(self.config.initial_delay)

            # Encode text in base64 for safer transmission
            encoded_text = base64.b64encode(text.encode("utf-8")).decode("ascii")

            # JavaScript to paste from clipboard
            js_code = f"""
            (async function() {{
                try {{
                    const element = document.querySelector('{selector}');
                    if (!element) return false;

                    // Decode the text
                    const text = atob('{encoded_text}');

                    // Create and dispatch paste event
                    const data = new DataTransfer();
                    data.items.add(new File([text], 'clipboard', {{ type: 'text/plain' }}));

                    const event = new ClipboardEvent('paste', {{
                        clipboardData: data,
                        bubbles: true
                    }});

                    element.dispatchEvent(event);

                    // Set value directly as backup
                    element.value = text;
                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));

                    return true;
                }} catch (e) {{
                    console.error('Paste error:', e);
                    return false;
                }}
            }})()
            """

            result = await self.page.evaluate(js_code)
            return result is True

        except Exception as e:
            print(f"Error pasting via clipboard: {e}")
            return False

    async def _verify_text(self, selector: str, expected_text: str) -> bool:
        """
        Verify that the correct text was entered in the field.

        Args:
            selector: CSS selector for the input field
            expected_text: The text that should have been entered

        Returns:
            True if the entered text matches expected text
        """
        try:
            element = await self.page.find(selector)
            if not element:
                return False

            # Get current value
            current_value = await element.get_attribute("value")

            if current_value == expected_text:
                return True

            # Log mismatch for debugging
            print(
                f"Text verification failed.\n"
                f"Expected: {repr(expected_text)}\n"
                f"Got: {repr(current_value)}"
            )

            return False

        except Exception as e:
            print(f"Error verifying text: {e}")
            return False

    async def type_with_retry(
        self,
        selector: str,
        text: str,
        strategy: Optional[TypingStrategy] = None,
    ) -> bool:
        """
        Type text with automatic retry on failure.

        This method wraps type_in_field with retry logic, useful for
        flaky input fields.

        Args:
            selector: CSS selector for the input field
            text: Text to type
            strategy: Override default strategy

        Returns:
            True if text was successfully entered after retries
        """
        for attempt in range(1, self.config.retry_count + 1):
            try:
                success = await self.type_in_field(selector, text, strategy)
                if success:
                    return True

                if attempt < self.config.retry_count:
                    # Wait before retry with exponential backoff
                    wait_time = attempt * 0.5
                    await asyncio.sleep(wait_time)

            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                if attempt < self.config.retry_count:
                    await asyncio.sleep(0.5)

        return False

    async def type_with_special_keys(
        self,
        selector: str,
        text: str,
        modifiers: Optional[list[str]] = None,
    ) -> bool:
        """
        Type text with modifier keys (Shift, Control, Alt, Meta).

        Args:
            selector: CSS selector for the input field
            text: Text to type
            modifiers: List of modifier keys to hold down

        Returns:
            True if typing was successful
        """
        try:
            element = await self.page.find(selector)
            if not element:
                return False

            await element.focus()
            await asyncio.sleep(self.config.initial_delay)

            if modifiers:
                # Press modifier keys
                for modifier in modifiers:
                    await element.press(modifier)
                    await asyncio.sleep(self.config.key_down_delay)

            # Type the text
            for char in text:
                if char == "\n":
                    await element.press("Enter")
                else:
                    await element.type(char)
                    await asyncio.sleep(self.config.char_delay)

            # Release modifier keys
            if modifiers:
                for modifier in reversed(modifiers):
                    await element.press(modifier)
                    await asyncio.sleep(self.config.key_down_delay)

            return True

        except Exception as e:
            print(f"Error typing with special keys: {e}")
            return False

    async def clear_and_type(
        self,
        selector: str,
        text: str,
        strategy: Optional[TypingStrategy] = None,
    ) -> bool:
        """
        Clear an input field and type new text (convenience method).

        Args:
            selector: CSS selector for the input field
            text: Text to type
            strategy: Override default strategy

        Returns:
            True if operation was successful
        """
        success = await self._clear_field(selector)
        if not success:
            return False

        return await self.type_in_field(selector, text, strategy)

    async def get_field_value(self, selector: str) -> Optional[str]:
        """
        Get the current value of an input field.

        Args:
            selector: CSS selector for the input field

        Returns:
            The field's value or None if not found
        """
        try:
            element = await self.page.find(selector)
            if not element:
                return None

            return await element.get_attribute("value")

        except Exception as e:
            print(f"Error getting field value: {e}")
            return None


async def example_safe_typing() -> None:
    """
    Example demonstrating SafeTyper usage with different strategies.

    This example shows how to use the SafeTyper class with various
    input scenarios and strategies.
    """
    try:
        # Import here to avoid circular dependency
        from quick_start import create_browser, BrowserConfig
    except ImportError:
        print("Error: quick_start module not found. Make sure it's in the same directory.")
        return

    # Create browser
    config = BrowserConfig(headless=False)
    browser = await create_browser(config, verbose=True)

    try:
        # Navigate to test page
        print("\nNavigating to example form...")
        page = await browser.get("https://example.com")
        await asyncio.sleep(2)

        # Create SafeTyper instance
        typer = SafeTyper(page)

        # Example 1: Simple text input
        print("\n[Example 1] Character-by-character typing")
        print("-" * 50)
        # Note: Replace selector with actual form field
        # success = await typer.type_in_field("#name-input", "John Doe")
        # print(f"Text input result: {success}")

        # Example 2: With retry logic
        print("\n[Example 2] Typing with automatic retry")
        print("-" * 50)
        # success = await typer.type_with_retry("#email-input", "user@example.com")
        # print(f"Type with retry result: {success}")

        # Example 3: Different strategy
        print("\n[Example 3] JavaScript injection strategy")
        print("-" * 50)
        # success = await typer.type_in_field(
        #     "#search-input",
        #     "test search query",
        #     strategy=TypingStrategy.JAVASCRIPT_INJECT
        # )
        # print(f"JavaScript injection result: {success}")

        # Example 4: Get field value
        print("\n[Example 4] Reading field values")
        print("-" * 50)
        # value = await typer.get_field_value("#name-input")
        # print(f"Field value: {value}")

        print("\nExamples completed (selectors need to be adapted to actual form)")

    finally:
        await browser.aclose()


def main() -> None:
    """Run examples."""
    print("SafeTyper - Reliable Text Input for nodriver")
    print("=" * 50)

    try:
        asyncio.run(example_safe_typing())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except ImportError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
