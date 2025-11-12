"""
Browser navigation utilities for Perplexity.ai

This module handles post-search navigation actions like starting new chats.
Uses SmartClicker for reliable element interaction with multiple fallback strategies.
"""
import json
import logging
from typing import Any, Optional

from src.browser.smart_click import SmartClicker
from src.browser.interactions import human_delay, find_interactive_element
from src.config import NEW_CHAT_CONFIG, TIMEOUTS

logger = logging.getLogger(__name__)


async def navigate_to_new_chat(page: Any, verify: bool = True, previous_url: Optional[str] = None) -> bool:
    """
    Navigate to a new chat by clicking the new chat button.

    This function finds and clicks the "New Thread" button (+ icon) in the
    Perplexity.ai sidebar to start a fresh chat session. It uses SmartClicker
    with multiple fallback strategies for maximum reliability.

    Args:
        page: Nodriver page/tab object (nodriver Tab instance)
        verify: Whether to verify navigation succeeded (default: True)
        previous_url: Previous page URL for independent verification (optional)
                     If provided, will check that page.url changed after navigation

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
        - If previous_url provided, logs URL change for debugging
    """
    logger.info("Navigating to new chat...")
    if previous_url:
        logger.debug(f"Previous URL stored for verification: {previous_url}")

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
            verification_passed = await verify_new_chat_page(
                page,
                previous_url=previous_url
            )

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


async def verify_new_chat_page(
    page: Any,
    timeout: float = None,
    previous_url: str = None
) -> bool:
    """
    Verify that we're actually on a new chat page.

    Performs multiple checks to prevent false positives from weak verification:
    1. URL changed to new chat pattern or root path
    2. Previous search results have disappeared
    3. Search input is present and empty

    All checks must pass for verification to succeed. This prevents false positives
    where old search pages might still have empty contenteditable elements.

    Args:
        page: Nodriver page/tab object (nodriver Tab instance)
        timeout: Max seconds to wait (default from config)
        previous_url: URL before navigation (for comparison)

    Returns:
        bool: True if ALL verification checks pass, False otherwise

    Example:
        >>> previous_url = page.url
        >>> # ... navigate to new chat ...
        >>> success = await verify_new_chat_page(page, previous_url=previous_url)
        >>> if success:
        ...     print("Successfully on new chat page")

    Notes:
        - Requires ALL checks to pass (URL, old content gone, new input present)
        - URL verification helps confirm page navigation occurred
        - Old content check prevents false positives on search result pages
        - Input presence check ensures search functionality is available
        - Uses try/except for safety - verification fails safely without exceptions
    """
    timeout = timeout or NEW_CHAT_CONFIG.get('timeout', TIMEOUTS['new_chat_navigation'])
    logger.info("Verifying new chat page (multi-check verification)...")

    checks_passed = []

    try:
        # ===== Check 1: URL Verification =====
        current_url = page.url
        logger.debug(f"Current URL: {current_url}")

        # Check if URL changed from previous
        if previous_url:
            url_changed = current_url != previous_url
            checks_passed.append(('URL changed', url_changed))
            logger.debug(f"URL changed from '{previous_url}': {url_changed}")
        else:
            logger.debug("Previous URL not provided, skipping URL change check")

        # Check if URL matches new chat pattern
        is_new_chat_url = _is_new_chat_url(current_url)
        checks_passed.append(('URL matches new chat pattern', is_new_chat_url))
        logger.debug(f"URL matches new chat pattern: {is_new_chat_url}")

        # ===== Check 2: Previous Content Gone =====
        old_content_gone = await _verify_old_content_gone(page, timeout)
        checks_passed.append(('Old search results gone', old_content_gone))
        logger.debug(f"Old content verification: {old_content_gone}")

        # ===== Check 3: Search Input Present and Empty =====
        input_found = False
        input_empty = False

        verification_selectors = NEW_CHAT_CONFIG.get('verification_selectors', [
            '[contenteditable="true"]',
            'textarea[placeholder*="Ask"]',
        ])

        logger.debug(
            f"Checking for search input with {len(verification_selectors)} selectors"
        )

        for selector in verification_selectors:
            try:
                element = await find_interactive_element(
                    page,
                    [selector],
                    timeout=timeout
                )

                if element:
                    input_found = True
                    input_value = await _get_input_value(element)
                    input_empty = not input_value or not input_value.strip()

                    logger.debug(
                        f"Search input found (selector: {selector}), "
                        f"empty: {input_empty}"
                    )
                    break
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        checks_passed.append(('Search input found', input_found))
        checks_passed.append(('Search input empty', input_empty))

        # ===== Evaluate All Checks =====
        all_passed = all(passed for _, passed in checks_passed)

        # Log detailed summary
        logger.info("New chat verification checks:")
        for check_name, passed in checks_passed:
            status = "PASS" if passed else "FAIL"
            logger.info(f"  [{status}] {check_name}")

        if all_passed:
            logger.info("New chat page verification: SUCCESS - All checks passed")
            return True
        else:
            failed_checks = [name for name, passed in checks_passed if not passed]
            logger.warning(
                f"New chat page verification: FAILED - {len(failed_checks)} "
                f"check(s) failed: {', '.join(failed_checks)}"
            )
            return False

    except Exception as e:
        logger.error(
            f"Error during new chat verification: {type(e).__name__}: {e}"
        )
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


def _is_new_chat_url(url: str) -> bool:
    """
    Check if URL matches new chat page pattern.

    New chat pages have URLs like:
    - https://www.perplexity.ai/ (root)
    - https://www.perplexity.ai/search/[thread-id]
    - https://www.perplexity.ai

    Args:
        url: Current page URL

    Returns:
        bool: True if URL matches new chat pattern
    """
    if not url:
        return False

    # Remove protocol and trailing slashes for comparison
    url_clean = url.replace('https://', '').replace('http://', '').rstrip('/')

    # Check for root path
    if url_clean == 'www.perplexity.ai' or url_clean == 'perplexity.ai':
        logger.debug("URL is root path (new chat)")
        return True

    # Check for /search/ path (new search thread)
    if '/search/' in url:
        logger.debug("URL contains /search/ path (new search thread)")
        return True

    logger.debug(f"URL does not match new chat pattern: {url}")
    return False


async def _verify_old_content_gone(page: Any, timeout: float) -> bool:
    """
    Verify that previous search results have disappeared.

    Checks for common result page elements that should NOT exist on a new chat:
    - Answer containers
    - Source citations
    - "ask a follow-up" UI elements
    - Previous response containers

    Args:
        page: Nodriver page instance
        timeout: Timeout for element selection

    Returns:
        bool: True if no old content found (page is empty), False if old content exists
    """
    # Selectors for elements that indicate a search result page
    old_content_selectors = [
        '[data-testid*="answer"]',          # Answer container
        '[data-testid*="source"]',          # Source citations
        '[class*="answer"]',                # CSS class-based answer
        '[class*="response"]',              # Response container
        'main [class*="text-base"]',        # Response text (Perplexity specific)
    ]

    # Text patterns that indicate a search result page
    old_content_text_patterns = [
        'ask a follow-up',
        'ask follow-up',
    ]

    logger.debug(f"Checking for old content with {len(old_content_selectors)} selectors")

    # Check each selector
    for selector in old_content_selectors:
        try:
            elements = await page.select_all(selector)
            if elements:
                logger.debug(f"Found old content with selector: {selector}")
                return False
        except Exception as e:
            logger.debug(f"Selector check failed ('{selector}'): {e}")
            continue

    # Check for text patterns
    logger.debug(f"Checking for old content with {len(old_content_text_patterns)} text patterns")
    for pattern in old_content_text_patterns:
        try:
            # Safely escape pattern for JavaScript interpolation
            escaped_pattern = json.dumps(pattern.lower())

            # Use JavaScript to check if text exists on page
            result = await page.evaluate(f'''
                document.body.innerText.toLowerCase().includes({escaped_pattern})
            ''')
            if result:
                logger.debug(f"Found old content text pattern: '{pattern}'")
                return False
        except Exception as e:
            logger.debug(f"Text pattern check failed ('{pattern}'): {type(e).__name__}: {e}")
            continue

    logger.debug("No old content found - page appears empty")
    return True
