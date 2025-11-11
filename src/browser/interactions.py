"""
Browser interaction utilities for human-like behavior and element handling
"""
import asyncio
import random
import logging
from typing import List, Dict, Any, Optional
from src.config import HUMAN_BEHAVIOR, TIMEOUTS

logger = logging.getLogger(__name__)


async def human_delay(delay_type: str = 'short') -> None:
    """
    Add human-like random delays to avoid detection

    Args:
        delay_type: 'short', 'medium', or 'long'
    """
    delays = HUMAN_BEHAVIOR['delays']

    if delay_type == 'short':
        delay = random.uniform(delays['short_min'], delays['short_max'])
    elif delay_type == 'medium':
        delay = random.uniform(delays['medium_min'], delays['medium_max'])
    elif delay_type == 'long':
        delay = random.uniform(delays['long_min'], delays['long_max'])
    else:
        delay = random.uniform(delays['short_min'], delays['short_max'])

    await asyncio.sleep(delay)


async def type_like_human(element, text: str) -> None:
    """
    Type text character-by-character with human-like delays

    Args:
        element: Element to type into
        text: Text to type
    """
    typing_speed = HUMAN_BEHAVIOR['typing_speed']

    for char in text:
        await element.send_keys(char)

        # Longer delay for spaces (more realistic)
        if char == ' ':
            delay = random.uniform(typing_speed['space_min'], typing_speed['space_max'])
        else:
            delay = random.uniform(typing_speed['char_min'], typing_speed['char_max'])

        await asyncio.sleep(delay)


async def find_interactive_element(page, selectors: List[str], timeout: int = None):
    """
    Find an interactive element with visibility and interactability checks

    Args:
        page: Nodriver page object
        selectors: List of CSS selectors to try
        timeout: Timeout for element selection

    Returns:
        Element if found and interactive, None otherwise
    """
    if timeout is None:
        timeout = TIMEOUTS['element_select']

    for selector in selectors:
        try:
            element = await page.select(selector, timeout=timeout)
            if element:
                # Check if element is visible and enabled
                try:
                    # Try to get element properties
                    is_visible = await page.evaluate(
                        f'document.querySelector("{selector}") !== null && '
                        f'window.getComputedStyle(document.querySelector("{selector}")).display !== "none" && '
                        f'window.getComputedStyle(document.querySelector("{selector}")).visibility !== "hidden"'
                    )

                    if is_visible:
                        logger.debug(f"Found interactive element: {selector}")
                        return element
                except:
                    # If we can't check visibility, assume it's visible
                    logger.debug(f"Found element (visibility check skipped): {selector}")
                    return element
        except:
            continue

    return None


async def health_check(page) -> Dict[str, Any]:
    """
    Perform health check on current page state

    Returns:
        Dictionary with health check results
    """
    health = {
        'url': page.url if hasattr(page, 'url') else None,
        'title': None,
        'responsive': False,
        'main_content_present': False,
    }

    try:
        # Check if page is responsive
        try:
            health['title'] = await page.evaluate('document.title')
            health['responsive'] = True
        except:
            pass

        # Check if main content is present
        try:
            main = await page.select('main', timeout=2)
            health['main_content_present'] = main is not None
        except:
            pass

    except Exception as e:
        logger.warning(f"Health check error: {e}")

    return health