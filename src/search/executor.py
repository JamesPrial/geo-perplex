"""
Search execution and content stability detection for Perplexity.ai

This module handles:
- Search query execution with human-like behavior
- Triple fallback search submission (newline, CDP Enter key, smart button click)
- Content stability detection using hash-based monitoring
"""
import asyncio
import hashlib
import logging
from time import time
from typing import Optional
import nodriver as uc

from src.config import SELECTORS, TIMEOUTS, STABILITY_CONFIG
from src.browser.interactions import find_interactive_element, human_delay, type_like_human
from src.browser.smart_click import SmartClicker, ClickStrategy
from src.types import NodriverPage

logger = logging.getLogger(__name__)

# Constants for search verification
# Quick element check timeout - fail fast if element not immediately visible
VERIFICATION_ELEMENT_TIMEOUT = 0.5


async def perform_search(page: NodriverPage, query: str) -> None:
    """
    Perform a search query on Perplexity.ai with human-like behavior

    Args:
        page: Nodriver page object
        query: Search query string

    Raises:
        Exception: If search cannot be performed
    """
    try:
        # Find search input using helper function
        search_input = await find_interactive_element(
            page,
            SELECTORS['search_input'],
            timeout=TIMEOUTS['element_select']
        )

        if not search_input:
            raise Exception('Could not find search input element')

        logger.info('Found search input')

        # Use SmartClicker to click and focus the input
        clicker = SmartClicker(page, verify_click=False, human_like_delay=True)

        # Try to click search input with smart strategies
        click_result = await clicker.click(
            SELECTORS['search_input'][0],  # Use first selector
            timeout=5.0
        )

        if not click_result.success:
            # Fallback to direct click if SmartClicker fails
            logger.warning(f'SmartClicker failed: {click_result.error}, using direct click')
            await search_input.click()
        else:
            logger.debug(f'Search input clicked using {click_result.strategy_used.value}')

        await human_delay('short')

        # Detect if element is contenteditable (verification unreliable for these)
        is_contenteditable = False
        try:
            contenteditable_attr = await search_input.get_attribute('contenteditable')
            is_contenteditable = contenteditable_attr is not None and contenteditable_attr == 'true'
            if is_contenteditable:
                logger.info("Search input is contenteditable, skipping typing verification (unreliable)")
        except Exception:
            pass

        # Type the query character-by-character (most realistic) with conditional verification
        logger.info(f'Typing query: "{query}"')
        typing_success = await type_like_human(
            search_input,
            query,
            page=page,  # Pass page for contenteditable support
            verify=not is_contenteditable  # Skip verification for contenteditable
        )

        if not typing_success and not is_contenteditable:
            # Only treat as error if verification was enabled and failed
            logger.error('Typing verification failed for standard input element')
            raise RuntimeError('Failed to type search query')
        elif not typing_success and is_contenteditable:
            logger.warning('Typing verification inconclusive for contenteditable element, continuing...')

        logger.info('Query entered')

        # Human delay before submitting
        await human_delay('short')

        # Capture URL before submission for verification
        original_url = page.url
        logger.debug(f'URL before submission: {original_url}')

        # Submit the search using triple fallback approach
        # Method 1: Send newline character
        await search_input.send_keys('\n')
        logger.debug('Sent newline character')

        # Wait briefly for initial response
        await human_delay('short')

        # Method 2: Try using CDP to send Enter key event directly
        try:
            await page.send(uc.cdp.input_.dispatch_key_event(
                type_='keyDown',
                key='Enter',
                code='Enter',
                windows_virtual_key_code=13,
                native_virtual_key_code=13
            ))
            await page.send(uc.cdp.input_.dispatch_key_event(
                type_='keyUp',
                key='Enter',
                code='Enter',
                windows_virtual_key_code=13,
                native_virtual_key_code=13
            ))
            logger.debug('Sent Enter key event via CDP')
        except Exception as e:
            logger.debug(f'CDP Enter key fallback error: {e}')

        # Wait for search to register
        await human_delay('medium')

        # Method 3: Fallback - use SmartClicker for search button if Enter didn't work
        try:
            # Try to find search button
            search_button = await find_interactive_element(
                page,
                SELECTORS['search_button'],
                timeout=2
            )

            if search_button:
                logger.debug('Found search button, using SmartClicker as fallback')
                button_result = await clicker.click(
                    SELECTORS['search_button'][0],
                    timeout=3.0
                )

                if button_result.success:
                    logger.debug(f'Button clicked using {button_result.strategy_used.value}')
                else:
                    logger.debug(f'SmartClicker button failed: {button_result.error}')

                await human_delay('short')
        except Exception as e:
            logger.debug(f'Search button fallback not needed: {e}')

        # Verify that search actually submitted
        logger.info('Verifying search submission...')
        submission_verified = await verify_search_submitted(
            page,
            original_url=original_url,
            timeout=5.0
        )

        if not submission_verified:
            logger.error('Search submission could not be verified - no loading indicators or URL change detected')
            raise RuntimeError('Search submission verification failed')

        logger.info('Search submitted and verified successfully')

    except Exception as error:
        raise Exception(f'Failed to perform search: {str(error)}')


async def verify_search_submitted(
    page: NodriverPage,
    original_url: str,
    timeout: float = 5.0
) -> bool:
    """
    Verify that search submission actually started.

    Checks multiple indicators that search is executing:
    1. URL changed (query parameters added)
    2. Loading indicators present
    3. Result generation UI visible

    Uses module-level VERIFICATION_ELEMENT_TIMEOUT for quick element checks.

    Args:
        page: Nodriver page instance
        original_url: URL before search submission
        timeout: Max seconds to wait for indicators

    Returns:
        True if search submission verified
    """
    logger.debug("Verifying search submission...")
    start_time = time()

    indicators_found = []

    while time() - start_time < timeout:
        # Check 1: URL changed
        current_url = page.url
        if current_url != original_url:
            logger.debug(f"URL changed: {original_url} → {current_url}")
            indicators_found.append('URL changed')

        # Check 2: Loading indicators
        loading_selectors = [
            '[data-testid*="loading"]',
            '[class*="loading"]',
            '[class*="spinner"]',
            'text:Searching',
            'text:Thinking',
        ]

        for selector in loading_selectors:
            try:
                element = await page.find(selector, timeout=VERIFICATION_ELEMENT_TIMEOUT)
                if element:
                    logger.debug(f"Found loading indicator: {selector}")
                    indicators_found.append(f'Loading indicator ({selector})')
                    break
            except Exception:
                continue

        # Check 3: Result generation UI
        result_selectors = [
            '[data-testid*="answer"]',
            '[data-testid*="result"]',
            '[class*="answer"]',
            'text:1 step',
            'text:completed',
        ]

        for selector in result_selectors:
            try:
                element = await page.find(selector, timeout=VERIFICATION_ELEMENT_TIMEOUT)
                if element:
                    logger.debug(f"Found result generation UI: {selector}")
                    indicators_found.append(f'Result UI ({selector})')
                    break
            except Exception:
                continue

        # If we found any indicators, search has started
        if indicators_found:
            logger.info(f"Search submission verified: {', '.join(indicators_found)}")
            return True

        await asyncio.sleep(0.3)

    logger.warning(f"Search submission verification timed out after {timeout}s - no indicators found")
    return False


async def wait_for_content_stability(page: NodriverPage, max_wait: Optional[int] = None) -> bool:
    """
    Wait for answer content to stabilize using multiple indicators

    This function monitors the main content area for stability using:
    - Hash-based change detection (MD5)
    - Content length tracking
    - Configurable stability threshold

    Args:
        page: Nodriver page object
        max_wait: Maximum time to wait (defaults to STABILITY_CONFIG, seconds)

    Returns:
        True if content stabilized, False if timeout reached
    """
    if max_wait is None:
        max_wait = TIMEOUTS['content_stability']

    logger.info('Waiting for answer to be generated...')

    check_interval = STABILITY_CONFIG['check_interval']
    stable_threshold = STABILITY_CONFIG['stable_threshold']
    min_content_length = STABILITY_CONFIG['min_content_length']

    stable_count = 0
    last_length = 0
    last_hash = ""

    start_time = asyncio.get_event_loop().time()

    while (asyncio.get_event_loop().time() - start_time) < max_wait:
        try:
            # Get main content
            main_content = await page.select('main', timeout=2)
            if not main_content:
                await asyncio.sleep(check_interval)
                continue

            # Use text_all to get full content (no await!)
            current_text = main_content.text_all
            current_length = len(current_text) if current_text else 0

            # Use hash for better change detection (catches small edits)
            current_hash = hashlib.md5(current_text.encode()).hexdigest() if current_text else ""

            # Check if content meets minimum threshold and has stabilized
            if current_length >= min_content_length:
                # Content is substantial, check if stable
                if current_hash == last_hash and current_length == last_length:
                    stable_count += 1
                    if stable_count >= stable_threshold:
                        logger.info(f'Answer generation complete (content stable at {current_length} chars)')
                        return True
                else:
                    # Content changed, reset counter
                    stable_count = 0
                    last_hash = current_hash
                    last_length = current_length
                    logger.debug(f'Content changing: {current_length} chars')
            else:
                # Not enough content yet
                stable_count = 0
                last_hash = current_hash
                last_length = current_length

        except Exception as e:
            logger.debug(f'Stability check error: {e}')

        await asyncio.sleep(check_interval)

    # Timeout reached
    logger.warning(f'Timeout after {max_wait}s, proceeding with current content...')
    return False
