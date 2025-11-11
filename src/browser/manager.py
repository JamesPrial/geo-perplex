"""
Browser lifecycle management and fingerprint randomization for Perplexity.ai automation
Handles browser launch, fingerprint randomization, and initialization with Nodriver
"""

from __future__ import annotations

import asyncio
import random
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional, AsyncIterator
from pathlib import Path
import nodriver as uc

from src.config import BROWSER_CONFIG, USER_AGENTS, VIEWPORT_SIZES, RETRY_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """
    Type-safe configuration for browser initialization.

    Attributes:
        headless: Run browser in headless mode (must be False for Perplexity)
        user_data_dir: Path to persistent browser profile directory
        disable_images: Disable image loading for faster performance
        window_width: Browser window width in pixels
        window_height: Browser window height in pixels
        user_agent: Custom user agent string (None = randomized)

    Examples:
        >>> config = BrowserConfig(headless=False, user_data_dir=Path('/tmp/profile'))
        >>> browser = await launch_browser(config)
    """
    headless: bool = False
    user_data_dir: Optional[Path] = None
    disable_images: bool = False
    window_width: int = 1920
    window_height: int = 1080
    user_agent: Optional[str] = None


def _build_browser_args(config: Optional[BrowserConfig] = None) -> tuple[list[str], str, tuple[int, int]]:
    """
    Build enhanced browser arguments with anti-detection features.

    Args:
        config: Optional BrowserConfig instance. If None, uses randomized defaults.

    Returns:
        Tuple of (args_list, user_agent, (width, height))

    Note:
        Includes critical anti-detection args to hide automation signals
    """
    # Randomize fingerprint if not provided
    if config and config.user_agent:
        user_agent = config.user_agent
    else:
        user_agent = random.choice(USER_AGENTS)

    if config:
        width = config.window_width
        height = config.window_height
    else:
        selected_viewport = random.choice(VIEWPORT_SIZES)
        width = selected_viewport['width']
        height = selected_viewport['height']

    # Start with base config args
    args = BROWSER_CONFIG['args'].copy()

    # CRITICAL: Anti-detection arguments
    args.extend([
        '--disable-blink-features=AutomationControlled',  # Hides automation detection
        '--disable-plugins',
        '--disable-extensions',
        '--disable-component-extensions-with-background-pages',
        '--disable-features=Prerender2',
        '--disable-background-networking',
        '--disable-default-apps',
        '--disable-sync',
    ])

    # User agent and window size
    args.extend([
        f'--user-agent={user_agent}',
        f'--window-size={width},{height}',
    ])

    # Optional: User data directory for persistent profiles
    if config and config.user_data_dir:
        args.append(f'--user-data-dir={config.user_data_dir}')
        logger.debug(f"Using persistent profile: {config.user_data_dir}")

    # Optional: Disable images for performance
    if config and config.disable_images:
        args.append('--blink-settings=imagesEnabled=false')
        logger.debug("Image loading disabled")

    return args, user_agent, (width, height)


async def launch_browser(config: Optional[BrowserConfig] = None) -> uc.Browser:
    """
    Launch browser with enhanced anti-detection and retry logic.

    This function:
    - Implements retry logic with exponential backoff (3 attempts)
    - Adds critical anti-detection browser arguments
    - Randomizes user agent and viewport (unless provided in config)
    - Supports persistent browser profiles via user_data_dir
    - Launches browser in headed mode with comprehensive stealth features

    Args:
        config: Optional BrowserConfig for custom settings. If None, uses randomized defaults.

    Returns:
        uc.Browser: Nodriver browser instance ready for automation

    Raises:
        RuntimeError: If browser launch fails after all retry attempts

    Examples:
        >>> # Basic usage with randomized fingerprint
        >>> browser = await launch_browser()
        >>> page = browser.main_tab

        >>> # With persistent profile
        >>> config = BrowserConfig(user_data_dir=Path('/tmp/perplexity-profile'))
        >>> browser = await launch_browser(config)

        >>> # With custom user agent
        >>> config = BrowserConfig(user_agent='Mozilla/5.0 ...')
        >>> browser = await launch_browser(config)
    """
    # Build browser arguments
    args, user_agent, (width, height) = _build_browser_args(config)

    logger.info('Launching browser with enhanced anti-detection...')
    logger.debug(f"User-Agent: {user_agent[:60]}...")
    logger.debug(f"Viewport: {width}x{height}")
    logger.debug(f"Browser args count: {len(args)}")

    # Retry logic with exponential backoff
    max_attempts = RETRY_CONFIG['max_attempts']
    base_delay = RETRY_CONFIG['base_delay']
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"Launch attempt {attempt}/{max_attempts}")

            # Launch browser with comprehensive stealth args
            browser = await uc.start(
                headless=BROWSER_CONFIG['headless'],
                browser_args=args,
            )

            logger.info(f'Browser launched successfully (attempt {attempt})')
            return browser

        except (OSError, RuntimeError, Exception) as e:
            last_error = e
            logger.warning(f"Launch attempt {attempt} failed: {e}")

            if attempt < max_attempts:
                # Exponential backoff: 1s, 2s, 3s
                wait_time = base_delay * attempt
                logger.debug(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_attempts} launch attempts exhausted")

    # If we get here, all retries failed
    raise RuntimeError(
        f"Failed to launch browser after {max_attempts} attempts. "
        f"Last error: {last_error}. "
        "Ensure Chrome/Chromium is installed and accessible."
    ) from last_error


@asynccontextmanager
async def browser_context(
    config: Optional[BrowserConfig] = None
) -> AsyncIterator[uc.Browser]:
    """
    Async context manager for safe browser lifecycle management.

    Ensures browser is always properly closed, even if exceptions occur.

    Args:
        config: Optional browser configuration

    Yields:
        Browser instance

    Example:
        >>> async with browser_context() as browser:
        ...     page = browser.main_tab
        ...     await page.get('https://example.com')
        ...     # ... use browser ...
        ... # Browser automatically closed here

    Raises:
        RuntimeError: If browser launch fails after all retries
    """
    browser = None

    try:
        # Launch browser
        browser = await launch_browser(config)
        logger.info("Browser context entered successfully")

        # Yield browser for use in with-block
        yield browser

    finally:
        # Always cleanup, even on exceptions
        if browser:
            try:
                await browser.stop()
                logger.info("Browser closed cleanly via context manager")
            except Exception as e:
                logger.warning(f"Error closing browser in context manager: {e}")
        else:
            logger.debug("No browser to clean up in context manager")


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
