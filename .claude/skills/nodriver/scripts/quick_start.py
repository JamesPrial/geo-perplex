"""
Quick browser initialization module for nodriver.

This module provides a clean, reusable interface for initializing a browser
with nodriver, including anti-detection settings, configuration options, and
error handling for common startup issues.

Example:
    Basic async usage:
        >>> import asyncio
        >>> from quick_start import create_browser
        >>>
        >>> async def main():
        ...     browser = await create_browser()
        ...     try:
        ...         page = await browser.get("https://example.com")
        ...     finally:
        ...         await browser.aclose()
        >>>
        >>> asyncio.run(main())

    With custom configuration:
        >>> config = BrowserConfig(headless=False, user_data_dir="/tmp/profile")
        >>> browser = await create_browser(config)
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class BrowserConfig:
    """
    Configuration options for browser initialization.

    Attributes:
        headless: Run browser in headless mode (default: True)
        disable_images: Disable image loading for faster performance (default: False)
        user_data_dir: Path to user data directory for persistent profiles (default: None)
        headless_mode: Headless mode strategy - 'new' or 'old' (default: 'new')
        disable_blink_features: Disable specific Blink features for stealth (default: True)
        disable_web_security: Disable web security (default: False)
        disable_sync: Disable Chrome sync (default: True)
        sandbox: Enable sandbox (default: True)
        viewport_width: Browser viewport width (default: 1920)
        viewport_height: Browser viewport height (default: 1080)
        user_agent: Custom user agent string (default: None)
        disable_dev_shm_usage: Disable /dev/shm usage (useful in Docker) (default: False)
    """

    headless: bool = True
    disable_images: bool = False
    user_data_dir: Optional[Path] = None
    headless_mode: str = "new"
    disable_blink_features: bool = True
    disable_web_security: bool = False
    disable_sync: bool = True
    sandbox: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    disable_dev_shm_usage: bool = False


def _build_launch_args(config: BrowserConfig) -> list[str]:
    """
    Build Chrome launch arguments from configuration.

    Args:
        config: BrowserConfig instance with desired settings

    Returns:
        List of command-line arguments for Chrome launcher

    Note:
        This function builds arguments optimized for anti-detection and stealth.
        These settings help avoid detection by anti-bot systems.
    """
    args = []

    # Headless mode configuration
    if config.headless:
        args.append(f"--headless={config.headless_mode}")

    # Anti-detection settings
    if config.disable_blink_features:
        args.append("--disable-blink-features=AutomationControlled")

    # Performance and security settings
    if config.disable_images:
        args.append("--blink-settings=imagesEnabled=false")

    if not config.sandbox:
        args.append("--no-sandbox")

    if config.disable_dev_shm_usage:
        args.append("--disable-dev-shm-usage")

    if not config.disable_web_security:
        args.append("--disable-web-security")

    if config.disable_sync:
        args.append("--disable-sync")

    # Viewport configuration (passed separately, not as args)
    # Window size is more reliable than viewport
    args.append(f"--window-size={config.viewport_width},{config.viewport_height}")

    # User data directory
    if config.user_data_dir:
        args.append(f"--user-data-dir={config.user_data_dir}")

    # Additional stealth features
    args.extend([
        "--disable-plugins",
        "--disable-extensions",
        "--disable-component-extensions-with-background-pages",
        "--disable-features=Prerender2",
    ])

    return args


async def create_browser(
    config: Optional[BrowserConfig] = None,
    verbose: bool = False,
) -> "nodriver.Browser":
    """
    Initialize and return a nodriver browser instance.

    This function handles browser initialization with sensible defaults and
    anti-detection settings. It manages common startup issues gracefully.

    Args:
        config: BrowserConfig instance. If None, uses default configuration.
        verbose: Enable verbose logging for debugging (default: False)

    Returns:
        Initialized nodriver.Browser instance

    Raises:
        RuntimeError: If browser initialization fails after retries
        ImportError: If nodriver is not installed

    Example:
        >>> config = BrowserConfig(headless=False, disable_images=True)
        >>> browser = await create_browser(config, verbose=True)
        >>> try:
        ...     page = await browser.get("https://example.com")
        ...     title = await page.title()
        ...     print(f"Page title: {title}")
        ... finally:
        ...     await browser.aclose()
    """

    # Import nodriver here to provide better error messaging
    try:
        import nodriver
    except ImportError:
        raise ImportError(
            "nodriver is not installed. Install it with: pip install nodriver"
        ) from None

    # Use default config if none provided
    if config is None:
        config = BrowserConfig()

    if verbose:
        print(f"[nodriver] Initializing browser with config: {config}")

    # Build launch arguments
    launch_args = _build_launch_args(config)

    if verbose:
        print(f"[nodriver] Launch arguments: {launch_args}")

    # Initialize browser with error handling
    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            if verbose:
                print(f"[nodriver] Launch attempt {attempt}/{max_retries}")

            browser = await nodriver.start(
                headless=config.headless,
                args=launch_args,
                user_agent=config.user_agent,
            )

            if verbose:
                print("[nodriver] Browser initialized successfully")

            return browser

        except (OSError, RuntimeError) as e:
            last_error = e
            if verbose:
                print(f"[nodriver] Attempt {attempt} failed: {e}")

            if attempt < max_retries:
                wait_time = attempt * 1  # Exponential backoff: 1s, 2s, 3s
                if verbose:
                    print(f"[nodriver] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                if verbose:
                    print("[nodriver] All retries exhausted")

    # If we get here, all retries failed
    raise RuntimeError(
        f"Failed to initialize browser after {max_retries} attempts. "
        f"Last error: {last_error}. "
        "Ensure Chrome/Chromium is installed and accessible."
    ) from last_error


async def quick_start_example() -> None:
    """
    Example demonstrating basic browser usage with proper error handling.

    This shows the recommended pattern for using the browser:
    1. Initialize browser with create_browser()
    2. Use try/finally to ensure cleanup
    3. Close browser when done
    """
    # Create browser with default settings
    browser = await create_browser(verbose=True)

    try:
        # Navigate to a website
        print("\nNavigating to example.com...")
        page = await browser.get("https://example.com")

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Get page content length
        content = await page.get_content()
        print(f"Page content length: {len(content)} bytes")

    except Exception as e:
        print(f"Error during browser operations: {e}")
        raise
    finally:
        # Always close the browser
        print("\nClosing browser...")
        await browser.aclose()


async def advanced_example() -> None:
    """
    Advanced example with custom configuration and headless mode disabled.

    This demonstrates:
    - Custom configuration options
    - User data directory for persistent state
    - Image loading disabled for faster performance
    """
    # Create custom configuration
    config = BrowserConfig(
        headless=False,  # Show browser window
        disable_images=True,  # Faster performance
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    )

    browser = await create_browser(config, verbose=True)

    try:
        # Navigate to website
        print("\nNavigating to example.com...")
        page = await browser.get("https://example.com")

        # Wait for specific element
        print("Waiting for page to load...")
        await asyncio.sleep(2)

        # Get page info
        title = await page.title()
        url = page.current_url
        print(f"Title: {title}")
        print(f"URL: {url}")

    finally:
        await browser.aclose()


def main() -> None:
    """
    Run example demonstrations.

    This function demonstrates both basic and advanced usage patterns.
    Uncomment the example you want to run.
    """
    print("nodriver Quick Start Examples")
    print("=" * 50)

    # Run basic example
    print("\n[1] Basic Example")
    print("-" * 50)
    asyncio.run(quick_start_example())

    # Run advanced example (commented out)
    # print("\n[2] Advanced Example")
    # print("-" * 50)
    # asyncio.run(advanced_example())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
