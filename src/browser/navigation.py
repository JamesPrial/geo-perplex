"""
Browser navigation utilities for Perplexity.ai

This module provides functions for navigating within Perplexity.ai,
such as starting new chats, going back, and other navigation actions.
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import nodriver as uc

from src.browser.interactions import human_delay, find_interactive_element, health_check
from src.config import SELECTORS, TIMEOUTS

logger = logging.getLogger(__name__)


async def start_new_chat(page: 'uc.Tab') -> bool:
    """
    Click the new chat button on Perplexity.ai sidebar.

    This function finds and clicks the "New Thread" button (+ icon) in the
    top-left sidebar of Perplexity.ai. It includes human-like delays and
    verifies the page state after clicking.

    The function tries multiple selector patterns for reliability:
    1. button[data-testid="sidebar-new-thread"] - Most specific
    2. button[aria-label="New Thread"] - Aria label fallback
    3. [data-testid="sidebar-new-thread"] - General fallback

    Args:
        page: Nodriver page/tab object

    Returns:
        bool: True if button was clicked successfully and page is responsive

    Raises:
        RuntimeError: If button not found or click operation failed

    Example:
        >>> browser = await uc.start()
        >>> page = await browser.get("https://www.perplexity.ai")
        >>> success = await start_new_chat(page)
        >>> if success:
        ...     print("Started new chat session")
    """
    logger.info("Starting new chat session...")

    # Find the new chat button using multiple selector patterns
    selectors = SELECTORS.get('navigation_buttons', [
        'button[data-testid="sidebar-new-thread"]',
        'button[aria-label="New Thread"]',
        '[data-testid="sidebar-new-thread"]',
    ])

    logger.debug(f"Looking for new chat button with selectors: {selectors}")

    button = await find_interactive_element(
        page,
        selectors=selectors,
        timeout=TIMEOUTS['element_select']
    )

    if not button:
        error_msg = (
            "New chat button not found in sidebar. "
            "Tried selectors: " + ", ".join(selectors)
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.debug("New chat button found")

    # Human-like delay before interaction (mimics real user behavior)
    await human_delay('short')

    # Click the button
    try:
        await button.click()
        logger.info("New chat button clicked successfully")
    except Exception as e:
        error_msg = f"Failed to click new chat button: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Wait for page transition/response
    await human_delay('short')

    # Verify page is still responsive after navigation
    health = await health_check(page)
    if not health['responsive']:
        logger.warning("Page not fully responsive after starting new chat")
        return False

    logger.debug("Page health check passed after new chat")
    return True
