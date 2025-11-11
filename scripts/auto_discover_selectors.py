"""
Automated Model Selector Discovery Script

This script programmatically inspects Perplexity.ai to find model selector elements.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.utils.cookies import load_cookies
from src.config import TIMEOUTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def find_potential_selectors(page):
    """Find all potential model selector elements."""

    logger.info("Searching for potential model selector elements...")

    # JavaScript to find elements that might be model selectors
    js_code = """
    () => {
        const results = [];

        // Search patterns for model-related elements
        const patterns = {
            text: ['model', 'focus', 'gpt', 'claude', 'sonar', 'select', 'switch'],
            attributes: ['data-testid', 'aria-label', 'aria-controls', 'role', 'class', 'id']
        };

        // Find all clickable elements
        const clickable = document.querySelectorAll('button, [role="button"], [role="combobox"], select, [class*="select"]');

        clickable.forEach(el => {
            const text = el.textContent?.toLowerCase() || '';
            const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
            const className = el.className?.toLowerCase() || '';
            const testId = el.getAttribute('data-testid')?.toLowerCase() || '';

            // Check if element matches model-related patterns
            const matchesPattern = patterns.text.some(pattern =>
                text.includes(pattern) ||
                ariaLabel.includes(pattern) ||
                className.includes(pattern) ||
                testId.includes(pattern)
            );

            if (matchesPattern || el.matches('[role="combobox"]')) {
                const info = {
                    tagName: el.tagName,
                    text: el.textContent?.trim().substring(0, 100),
                    attributes: {}
                };

                // Collect all relevant attributes
                patterns.attributes.forEach(attr => {
                    const value = el.getAttribute(attr);
                    if (value) {
                        info.attributes[attr] = value;
                    }
                });

                // Try to get a unique CSS selector
                try {
                    let selector = '';
                    if (info.attributes['data-testid']) {
                        selector = `[data-testid="${info.attributes['data-testid']}"]`;
                    } else if (info.attributes.id) {
                        selector = `#${info.attributes.id}`;
                    } else if (info.attributes.class) {
                        const classes = info.attributes.class.split(' ').slice(0, 2).join('.');
                        selector = `${el.tagName.toLowerCase()}.${classes}`;
                    }
                    info.selector = selector;
                } catch (e) {
                    info.selector = el.tagName.toLowerCase();
                }

                // Get position info
                const rect = el.getBoundingClientRect();
                info.position = {
                    top: Math.round(rect.top),
                    left: Math.round(rect.left),
                    visible: rect.width > 0 && rect.height > 0
                };

                results.push(info);
            }
        });

        return results;
    }
    """

    try:
        result = await page.evaluate(js_code)
        return result
    except Exception as e:
        logger.error(f"Error finding selectors: {e}")
        return []


async def find_model_options(page):
    """Find elements that look like model options in a menu/dropdown."""

    logger.info("Searching for model option elements...")

    js_code = """
    () => {
        const results = [];

        // Look for menu/listbox containers
        const containers = document.querySelectorAll('[role="menu"], [role="listbox"], [role="popup"], [class*="dropdown"], [class*="menu"]');

        containers.forEach(container => {
            // Find options within
            const options = container.querySelectorAll('[role="menuitem"], [role="option"], button, a, li');

            options.forEach(opt => {
                const text = opt.textContent?.trim();
                if (text && text.length < 50) {  // Reasonable length for model name
                    results.push({
                        text: text,
                        tagName: opt.tagName,
                        role: opt.getAttribute('role'),
                        testId: opt.getAttribute('data-testid'),
                        className: opt.className
                    });
                }
            });
        });

        return results;
    }
    """

    try:
        result = await page.evaluate(js_code)
        return result
    except Exception as e:
        logger.error(f"Error finding model options: {e}")
        return []


async def main():
    """Main discovery function."""

    logger.info("=" * 70)
    logger.info("Automated Model Selector Discovery")
    logger.info("=" * 70)
    logger.info("")

    # Load cookies
    logger.info("Step 1: Loading authentication cookies...")
    cookies = load_cookies()
    logger.info("Cookies loaded!")
    logger.info("")

    # Launch browser
    logger.info("Step 2: Launching browser...")
    browser = await launch_browser()
    page = await browser.get('about:blank')
    logger.info("Browser launched!")
    logger.info("")

    # Set cookies
    logger.info("Step 3: Setting authentication cookies...")
    await set_cookies(page, cookies)
    logger.info("Cookies set!")
    logger.info("")

    # Navigate to Perplexity
    logger.info("Step 4: Navigating to Perplexity.ai...")
    await page.get('https://www.perplexity.ai', new_tab=False)
    await asyncio.sleep(3)  # Wait for page to fully load
    logger.info("Navigation complete!")
    logger.info("")

    # Verify authentication
    logger.info("Step 5: Verifying authentication...")
    is_authenticated = await verify_authentication(page)
    if not is_authenticated:
        logger.error("Authentication failed!")
        return
    logger.info("Authenticated successfully!")
    logger.info("")

    # Find potential selectors
    logger.info("=" * 70)
    logger.info("DISCOVERING SELECTORS")
    logger.info("=" * 70)
    logger.info("")

    selectors = await find_potential_selectors(page)

    if selectors:
        logger.info(f"Found {len(selectors)} potential model selector elements:")
        logger.info("")

        for i, sel in enumerate(selectors, 1):
            logger.info(f"  [{i}] {sel['tagName']}")
            logger.info(f"      Text: {sel['text'][:80]}")
            if 'selector' in sel:
                logger.info(f"      Selector: {sel['selector']}")
            for attr, value in sel['attributes'].items():
                logger.info(f"      {attr}: {value}")
            logger.info(f"      Position: top={sel['position']['top']}, left={sel['position']['left']}, visible={sel['position']['visible']}")
            logger.info("")
    else:
        logger.warning("No potential selectors found!")

    # Find model options
    logger.info("=" * 70)
    logger.info("DISCOVERING MODEL OPTIONS")
    logger.info("=" * 70)
    logger.info("")

    options = await find_model_options(page)

    if options:
        logger.info(f"Found {len(options)} potential model options:")
        logger.info("")

        for i, opt in enumerate(options, 1):
            logger.info(f"  [{i}] {opt['text']}")
            logger.info(f"      Tag: {opt['tagName']}, Role: {opt['role']}")
            if opt.get('testId'):
                logger.info(f"      data-testid: {opt['testId']}")
            logger.info("")
    else:
        logger.warning("No model options found! (They may only appear after clicking selector)")

    # Keep browser open for manual verification
    logger.info("=" * 70)
    logger.info("BROWSER READY FOR MANUAL VERIFICATION")
    logger.info("=" * 70)
    logger.info("")
    logger.info("The browser will stay open for manual verification.")
    logger.info("Press Ctrl+C to close and exit.")
    logger.info("")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Closing browser...")
        browser.stop()


if __name__ == '__main__':
    asyncio.run(main())
