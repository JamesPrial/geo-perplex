#!/usr/bin/env python3
"""
Example usage of the browser manager module

This example demonstrates:
1. Launching a browser with randomized fingerprint
2. Using random user agent and viewport functions
3. Proper async/await patterns with Nodriver
4. Browser cleanup and resource management
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser import (
    launch_browser,
    get_random_user_agent,
    get_random_viewport,
)

# Configure logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_launch():
    """Example 1: Basic browser launch with randomized fingerprint"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 1: Basic Browser Launch")
    logger.info("=" * 70)

    browser = None
    try:
        # Launch browser with randomized fingerprint
        browser = await launch_browser()
        logger.info("Browser launched successfully!")

        # Get the main tab
        page = browser.main_tab
        logger.info(f"Main tab URL: {page.url}")

        # Demonstrate page operations
        logger.info("Browser is ready for automation")
        # Note: Actual navigation would require display server

    except Exception as e:
        logger.error(f"Error: {e}")
        if "display server" in str(e).lower():
            logger.warning("This example requires a display server (GUI environment)")
    finally:
        if browser:
            browser.stop()
            logger.info("Browser stopped")


async def example_fingerprint_functions():
    """Example 2: Using fingerprint randomization functions"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 2: Fingerprint Randomization Functions")
    logger.info("=" * 70)

    # Get random user agent multiple times
    logger.info("\nGenerating 3 random user agents:")
    for i in range(3):
        user_agent = get_random_user_agent()
        logger.info(f"  {i + 1}. {user_agent[:60]}...")

    # Get random viewport multiple times
    logger.info("\nGenerating 5 random viewports:")
    viewports = []
    for i in range(5):
        viewport = get_random_viewport()
        resolution = f"{viewport['width']}x{viewport['height']}"
        viewports.append(resolution)
        logger.info(f"  {i + 1}. {resolution}")

    # Show unique viewports generated
    unique_viewports = set(viewports)
    logger.info(f"\nUnique viewports generated: {len(unique_viewports)}")


async def example_multiple_sessions():
    """Example 3: Multiple browser sessions with different fingerprints"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 3: Multiple Browser Sessions")
    logger.info("=" * 70)

    browsers = []
    try:
        logger.info("Launching 2 browsers with different fingerprints...")
        for session_num in range(2):
            logger.info(f"\nSession {session_num + 1}:")
            browser = await launch_browser()
            browsers.append(browser)
            logger.info(f"  ✓ Browser {session_num + 1} launched")

        logger.info(f"\nTotal browsers active: {len(browsers)}")
        logger.info("Each has a unique randomized fingerprint")

    except Exception as e:
        logger.error(f"Error: {e}")
        if "display server" in str(e).lower():
            logger.warning("This example requires a display server (GUI environment)")
    finally:
        for i, browser in enumerate(browsers):
            if browser:
                browser.stop()
                logger.info(f"Browser {i + 1} stopped")


async def example_configuration_inspection():
    """Example 4: Inspect configuration values"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 4: Configuration Inspection")
    logger.info("=" * 70)

    from src.config import BROWSER_CONFIG, USER_AGENTS, VIEWPORT_SIZES

    logger.info("\nBrowser Configuration:")
    logger.info(f"  Headless mode: {BROWSER_CONFIG['headless']}")
    logger.info(f"  Browser args: {BROWSER_CONFIG['args']}")

    logger.info(f"\nUser Agents ({len(USER_AGENTS)} available):")
    for i, ua in enumerate(USER_AGENTS, 1):
        logger.info(f"  {i}. {ua[:60]}...")

    logger.info(f"\nViewport Sizes ({len(VIEWPORT_SIZES)} available):")
    for i, vp in enumerate(VIEWPORT_SIZES, 1):
        logger.info(f"  {i}. {vp['width']}x{vp['height']}")


async def example_error_handling():
    """Example 5: Error handling patterns"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 5: Error Handling")
    logger.info("=" * 70)

    try:
        logger.info("Attempting to launch browser...")
        browser = await launch_browser()
        # This will fail in non-GUI environment, but shows error handling
        browser.stop()
    except Exception as e:
        logger.error(f"Browser launch failed: {type(e).__name__}")
        logger.error(f"Error message: {e}")
        if "display" in str(e).lower():
            logger.info("Suggestion: Run this example in a GUI environment or with X11 forwarding")


async def main():
    """Run all examples"""
    logger.info("\n")
    logger.info("*" * 70)
    logger.info("BROWSER MANAGER MODULE EXAMPLES")
    logger.info("*" * 70)

    # Example 2 and 4 don't require display
    await example_fingerprint_functions()
    await example_configuration_inspection()

    # Examples 1, 3, 5 require display - will show errors if unavailable
    await example_basic_launch()
    await example_multiple_sessions()
    await example_error_handling()

    logger.info("\n")
    logger.info("*" * 70)
    logger.info("EXAMPLES COMPLETE")
    logger.info("*" * 70)
    logger.info("\nFor more information, see: docs/BROWSER_MANAGER.md")


if __name__ == '__main__':
    asyncio.run(main())
