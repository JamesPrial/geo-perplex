"""
Browser lifecycle management and fingerprint randomization for Perplexity.ai automation
Handles browser launch, fingerprint randomization, and initialization with Nodriver
"""
import random
import logging
from typing import Optional
import nodriver as uc

from src.config import BROWSER_CONFIG, USER_AGENTS, VIEWPORT_SIZES

logger = logging.getLogger(__name__)


async def launch_browser() -> uc.Browser:
    """
    Launch browser with randomized fingerprint for bot detection avoidance

    This function:
    - Randomizes user agent from USER_AGENTS pool
    - Randomizes viewport from VIEWPORT_SIZES pool
    - Launches browser in headed mode with fingerprint args
    - Logs selected fingerprint details for debugging

    Returns:
        uc.Browser: Nodriver browser instance ready for automation

    Raises:
        Exception: If browser launch fails

    Examples:
        >>> browser = await launch_browser()
        >>> page = browser.main_tab
        >>> # Use page for automation...
    """
    # Randomize fingerprint for each browser instance
    selected_user_agent = random.choice(USER_AGENTS)
    selected_viewport = random.choice(VIEWPORT_SIZES)

    logger.info('Launching browser (headed mode with fingerprint randomization)...')
    logger.debug(f"Selected User-Agent: {selected_user_agent[:50]}...")
    logger.debug(f"Selected viewport: {selected_viewport['width']}x{selected_viewport['height']}")

    try:
        # Launch browser with randomized fingerprint
        browser = await uc.start(
            headless=BROWSER_CONFIG['headless'],
            browser_args=BROWSER_CONFIG['args'] + [
                f'--user-agent={selected_user_agent}',
                f'--window-size={selected_viewport["width"]},{selected_viewport["height"]}',
            ]
        )

        logger.info('Browser launched successfully')
        return browser

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        raise


def get_random_user_agent() -> str:
    """
    Get a random user agent from the configured pool

    Returns:
        str: Random user agent string
    """
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """
    Get a random viewport size from the configured pool

    Returns:
        dict: Viewport dictionary with 'width' and 'height' keys

    Examples:
        >>> viewport = get_random_viewport()
        >>> print(f"{viewport['width']}x{viewport['height']}")
        1920x1080
    """
    return random.choice(VIEWPORT_SIZES)
