"""
Browser navigation utilities for Perplexity.ai

This module handles post-search navigation actions like starting new chats.
Uses SmartClicker for reliable element interaction with multiple fallback strategies.
"""
import logging
from typing import Any, Optional

from src.browser.smart_click import SmartClicker
from src.browser.interactions import human_delay, find_interactive_element
from src.config import NEW_CHAT_CONFIG, TIMEOUTS

logger = logging.getLogger(__name__)


async def navigate_to_new_chat(page: Any, verify: bool = True) -> bool:
    """
    Navigate to a new chat by clicking the new chat button.

    This function finds and clicks the "New Thread" button (+ icon) in the
    Perplexity.ai sidebar to start a fresh chat session. It uses SmartClicker
    with multiple fallback strategies for maximum reliability.

    Args:
        page: Nodriver page/tab object (nodriver Tab instance)
        verify: Whether to verify navigation succeeded (default: True)

    Returns:
        bool: True if navigation succeeded (and verified if requested), False otherwise

    Example:
        >>> browser = await uc.start()
        >>> page = await browser.get("https://www.perplexity.ai")
        >>> success = await navigate_to_new_chat(page, verify=True)
        >>> if success:
        ...     print("Successfully started new chat")
        ... else:
        ...     print("Failed to start new chat")

    Notes:
        - Uses human-like delays before interactions to avoid bot detection
        - Tries multiple selector patterns from NEW_CHAT_CONFIG
        - Uses SmartClicker with 6 fallback click strategies
        - Optional verification checks for empty search input
        - Returns False on verification failure (not an exception)
    """
    logger.info("Navigating to new chat...")

    try:
        # Get selectors from config
        selectors = NEW_CHAT_CONFIG.get('selectors', [
            'button[data-testid="sidebar-new-thread"]',
            'button[aria-label="New Thread"]',
            '[data-testid="sidebar-new-thread"]',
        ])

        logger.debug(f"Looking for new chat button with {len(selectors)} selector patterns")

        # Find the new chat button using multiple selector patterns
        button_element = None
        for selector in selectors:
            try:
                button_element = await find_interactive_element(
                    page,
                    selectors=[selector],
                    timeout=NEW_CHAT_CONFIG.get('timeout', TIMEOUTS['element_select'])
                )
                if button_element:
                    logger.debug(f"Found new chat button with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        if not button_element:
            error_msg = (
                "New chat button not found. "
                f"Tried {len(selectors)} selectors: {', '.join(selectors)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Add human-like delay before interaction
        logger.debug("Adding human-like delay before clicking...")
        await human_delay('short')

        # Click using SmartClicker for reliability
        logger.debug("Clicking new chat button with SmartClicker...")
        clicker = SmartClicker(
            page=page,
            verify_click=False,  # We'll do manual verification
            scroll_into_view=True,
            human_like_delay=True,
            max_retries=6
        )

        # Try to click with the first selector that found the element
        for selector in selectors:
            try:
                result = await clicker.click(
                    selector=selector,
                    timeout=NEW_CHAT_CONFIG.get('timeout', 5.0)
                )

                if result.success:
                    logger.info(
                        f"New chat button clicked successfully using "
                        f"{result.strategy_used.value} strategy (attempt {result.attempts})"
                    )
                    break
            except Exception as e:
                logger.debug(f"Click attempt with '{selector}' failed: {e}")
                continue
        else:
            # All selectors failed
            logger.error("Failed to click new chat button with all strategies")
            return False

        # Wait for navigation to complete
        logger.debug("Waiting for navigation to complete...")
        await human_delay('medium')

        # Verify navigation succeeded if requested
        if verify:
            logger.debug("Verifying new chat page loaded...")
            verification_passed = await verify_new_chat_page(page)

            if verification_passed:
                logger.info("New chat navigation verified successfully")
                return True
            else:
                logger.warning("New chat navigation verification failed")
                return False
        else:
            # No verification requested, assume success
            logger.info("New chat navigation completed (verification skipped)")
            return True

    except Exception as e:
        logger.error(f"Error during new chat navigation: {type(e).__name__}: {e}")
        if isinstance(e, RuntimeError):
            logger.error("New chat button not found - check NEW_CHAT_CONFIG selectors")
        return False


async def verify_new_chat_page(page: Any) -> bool:
    """
    Verify that the new chat page loaded correctly.

    Checks for empty search input using verification selectors from config.
    This confirms that navigation to a fresh chat succeeded.

    Args:
        page: Nodriver page/tab object (nodriver Tab instance)

    Returns:
        bool: True if new chat page verified, False otherwise

    Example:
        >>> success = await verify_new_chat_page(page)
        >>> if success:
        ...     print("On new chat page")

    Notes:
        - Checks multiple verification selectors from NEW_CHAT_CONFIG
        - Verifies input is actually empty (no text content)
        - Handles both .get_attribute('value') and .text_all properties
        - Uses try/except for safety (no exceptions raised)
        - Returns True if ANY verification selector confirms empty input
    """
    try:
        # Get verification selectors from config
        verification_selectors = NEW_CHAT_CONFIG.get('verification_selectors', [
            '[contenteditable="true"]',
            'textarea[placeholder*="Ask"]',
        ])

        logger.debug(
            f"Verifying new chat page with {len(verification_selectors)} selectors"
        )

        # Try each verification selector
        for selector in verification_selectors:
            try:
                element = await find_interactive_element(
                    page,
                    [selector],
                    timeout=NEW_CHAT_CONFIG.get('timeout', 3.0)
                )

                if element:
                    logger.debug(f"Found verification element: {selector}")

                    # Check if input is empty
                    input_value = await _get_input_value(element)

                    if input_value == "" or input_value is None:
                        logger.debug(
                            f"Verification passed: {selector} is empty"
                        )
                        return True
                    else:
                        logger.debug(
                            f"Verification check: {selector} has content: "
                            f"'{input_value[:50]}...'"
                        )
            except Exception as e:
                logger.debug(f"Verification selector '{selector}' failed: {e}")
                continue

        # None of the verification selectors confirmed empty input
        logger.warning("Could not verify new chat page - no empty input found")
        return False

    except Exception as e:
        logger.warning(f"Error during new chat verification: {type(e).__name__}: {e}")
        return False


async def _get_input_value(element) -> Optional[str]:
    """
    Safely get input value or text content from an element.

    Tries multiple methods to extract text from input/textarea elements:
    1. .get_attribute('value') - For input/textarea elements
    2. .text_all property - For contenteditable elements
    3. .text property - Fallback for direct text

    Args:
        element: Nodriver element

    Returns:
        str: Element value/text or None if not accessible

    Notes:
        - Handles both awaitable and non-awaitable attribute access
        - Safely handles AttributeError and TypeError
        - Returns None instead of raising exceptions
    """
    try:
        # Try value attribute first (for input/textarea)
        value = element.get_attribute('value')

        # Check if it's awaitable (depends on nodriver version)
        if hasattr(value, '__await__'):
            value = await value

        if value is not None:
            return str(value)
    except (AttributeError, TypeError) as e:
        logger.debug(f"Could not get 'value' attribute: {e}")

    # Fallback to text_all property (for contenteditable)
    try:
        if hasattr(element, 'text_all'):
            text_all = element.text_all  # Property, not async
            return text_all if text_all else ""
    except (AttributeError, TypeError) as e:
        logger.debug(f"Could not get 'text_all' property: {e}")

    # Fallback to text property
    try:
        if hasattr(element, 'text'):
            text = element.text  # Property, not async
            return text if text else ""
    except (AttributeError, TypeError) as e:
        logger.debug(f"Could not get 'text' property: {e}")

    return None
