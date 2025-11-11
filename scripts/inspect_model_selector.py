#!/usr/bin/env python3
"""
UI inspection script to discover Perplexity model selector elements.

This standalone script helps identify the correct CSS selectors and available models
for the model selection feature. It launches a browser, authenticates with cookies,
and presents Perplexity.ai for manual inspection via browser DevTools.

Usage:
    python scripts/inspect_model_selector.py

Instructions after script runs:
    1. The browser will open Perplexity.ai in headed mode
    2. Open DevTools (F12) and inspect the model selector UI
    3. Look for buttons/dropdowns that show model names (e.g., "GPT-4", "Claude", etc.)
    4. Note the CSS selectors, aria-labels, data-testid attributes, etc.
    5. Check the options container structure (menu, listbox, etc.)
    6. Update src/config.py with discovered selectors and available models
    7. Press Ctrl+C to close when done

Pay special attention to:
    - Where the model selector button is located
    - What text/attributes it has when no model is selected vs when one is selected
    - How the model options menu/dropdown appears
    - CSS selectors for each element
    - aria-labels or data-testid attributes
    - Text content of available model options
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cookies import load_cookies, validate_auth_cookies
from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.browser.interactions import health_check, human_delay
from src.config import LOGGING_CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


async def main():
    """Launch browser for UI inspection."""
    browser = None

    try:
        logger.info("=" * 70)
        logger.info("Perplexity Model Selector - UI Discovery Script")
        logger.info("=" * 70)
        logger.info("")
        logger.info("This script will:")
        logger.info("  1. Load authentication cookies from auth.json")
        logger.info("  2. Launch a browser and navigate to Perplexity.ai")
        logger.info("  3. Keep the browser open indefinitely for manual inspection")
        logger.info("")
        logger.info("What to do:")
        logger.info("  - Open DevTools (F12) when browser appears")
        logger.info("  - Inspect the model selector UI elements")
        logger.info("  - Note CSS selectors, aria-labels, data-testid attributes")
        logger.info("  - Check available model options and their text content")
        logger.info("  - Look for the options container (menu/listbox)")
        logger.info("")
        logger.info("When done inspecting:")
        logger.info("  - Update src/config.py with discovered selectors")
        logger.info("  - Press Ctrl+C to close the browser and exit")
        logger.info("")
        logger.info("-" * 70)
        logger.info("")

        # Step 1: Load and validate cookies
        logger.info("Step 1: Loading authentication cookies...")
        cookies = load_cookies()
        validate_auth_cookies(cookies)
        logger.info("Cookies loaded successfully!")
        logger.info("")

        # Step 2: Launch browser
        logger.info("Step 2: Launching browser in headed mode...")
        browser = await launch_browser()
        logger.info("Browser launched!")
        logger.info("")

        # Step 3: Get first page
        page = browser.main_tab

        # Step 4: Set cookies
        logger.info("Step 3: Setting authentication cookies...")
        await set_cookies(page, cookies)
        logger.info("Cookies injected!")
        logger.info("")

        # Step 5: Navigate to Perplexity
        logger.info("Step 4: Navigating to Perplexity.ai...")
        await page.get("https://www.perplexity.ai")
        await human_delay("medium")
        logger.info("Navigation complete!")
        logger.info("")

        # Perform health check
        health = await health_check(page)
        logger.debug(f"Page health: {health}")

        # Step 6: Verify authentication
        logger.info("Step 5: Verifying authentication...")
        is_authenticated = await verify_authentication(page)

        if not is_authenticated:
            raise Exception("Authentication failed - cookies may be expired or invalid")

        logger.info("Successfully authenticated!")
        logger.info("")

        # Now present the UI for inspection
        logger.info("=" * 70)
        logger.info("BROWSER IS NOW READY FOR INSPECTION")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Tips for inspection:")
        logger.info("")
        logger.info("1. MODEL SELECTOR BUTTON:")
        logger.info("   - Look for buttons or dropdowns showing model names")
        logger.info("   - May be in header, sidebar, or input area")
        logger.info("   - Common patterns: 'Select Model', 'Switch Model', model names like 'GPT-4'")
        logger.info("")
        logger.info("2. EXTRACTING SELECTORS:")
        logger.info("   - Right-click element → Inspect")
        logger.info("   - Look for attributes:")
        logger.info("     * data-testid (e.g., data-testid='model-selector')")
        logger.info("     * aria-label (e.g., aria-label='Select Model')")
        logger.info("     * class names (e.g., class='model-button')")
        logger.info("     * Exact CSS selector from DevTools 'Copy selector'")
        logger.info("")
        logger.info("3. MODEL OPTIONS:")
        logger.info("   - Click the selector to see available models")
        logger.info("   - Note all model names and their text content")
        logger.info("   - Check if they're in a menu ([role='menu']) or listbox ([role='listbox'])")
        logger.info("   - Look for individual option selectors")
        logger.info("")
        logger.info("4. USEFUL DEVTOOLS FEATURES:")
        logger.info("   - Element Picker (top-left of DevTools)")
        logger.info("   - Right-click 'Copy selector' for CSS selector")
        logger.info("   - Hover over elements in code to highlight in page")
        logger.info("")
        logger.info("-" * 70)
        logger.info("")
        logger.info("Press Ctrl+C when done inspecting to close and exit.")
        logger.info("")

        # Keep browser open indefinitely
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Closing browser...")
    except Exception as error:
        logger.error(f"Error: {str(error)}", exc_info=True)
        raise
    finally:
        # Cleanup
        if browser:
            logger.info("Cleaning up...")
            browser.stop()
            logger.info("Browser closed")
            logger.info("")
            logger.info("Remember to update src/config.py with discovered selectors!")
            logger.info("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInspection complete. Exiting.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
