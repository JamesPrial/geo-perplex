"""
Enhanced Model Selector Discovery with Screenshot

Takes screenshots and dumps all button/clickable elements to help find model selector.
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main discovery function with screenshot."""

    logger.info("=" * 70)
    logger.info("Enhanced Model Selector Discovery")
    logger.info("=" * 70)

    # Setup
    cookies = load_cookies()
    browser = await launch_browser()
    page = await browser.get('about:blank')
    await set_cookies(page, cookies)

    # Navigate
    logger.info("Navigating to Perplexity.ai...")
    await page.get('https://www.perplexity.ai', new_tab=False)
    await asyncio.sleep(4)  # Wait longer

    # Verify auth
    is_authenticated = await verify_authentication(page)
    if not is_authenticated:
        logger.error("Authentication failed!")
        return

    logger.info("Authenticated successfully!")

    # Take initial screenshot
    logger.info("Taking screenshot 1: Main page")
    await page.save_screenshot('screenshot_mainpage.png')

    # Dump ALL buttons and clickable elements
    logger.info("\nSearching for ALL clickable elements...")

    js_code = """
    () => {
        const results = [];
        const elements = document.querySelectorAll('button, [role="button"], [role="combobox"], a, select, input, [class*="select"], [class*="dropdown"], [class*="button"]');

        elements.forEach((el, idx) => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {  // Only visible elements
                results.push({
                    index: idx,
                    tag: el.tagName,
                    text: el.textContent?.trim().substring(0, 60) || '',
                    testId: el.getAttribute('data-testid') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    className: el.className?.substring(0, 80) || '',
                    role: el.getAttribute('role') || '',
                    id: el.id || '',
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
            }
        });

        return results;
    }
    """

    elements = await page.evaluate(js_code)

    logger.info(f"\nFound {len(elements)} visible clickable elements:")
    logger.info("=" * 70)

    for el in elements:
        if any(keyword in (el['text'].lower() + el['ariaLabel'].lower() + el['testId'].lower())
               for keyword in ['model', 'gpt', 'claude', 'select', 'pro', 'focus']):
            logger.info(f"\n[{el['index']}] {el['tag']} - INTERESTING!")
            logger.info(f"  Text: {el['text']}")
            if el['testId']:
                logger.info(f"  data-testid: {el['testId']}")
            if el['ariaLabel']:
                logger.info(f"  aria-label: {el['ariaLabel']}")
            if el['role']:
                logger.info(f"  role: {el['role']}")
            if el['className']:
                logger.info(f"  class: {el['className']}")
            logger.info(f"  Position: ({el['position']['left']}, {el['position']['top']}) {el['position']['width']}x{el['position']['height']}")

    # Also dump everything to a file
    with open('all_elements.txt', 'w') as f:
        for el in elements:
            f.write(f"\n{'='*70}\n")
            f.write(f"[{el['index']}] {el['tag']}\n")
            f.write(f"Text: {el['text']}\n")
            f.write(f"data-testid: {el['testId']}\n")
            f.write(f"aria-label: {el['ariaLabel']}\n")
            f.write(f"role: {el['role']}\n")
            f.write(f"class: {el['className']}\n")
            f.write(f"id: {el['id']}\n")
            f.write(f"Position: {el['position']}\n")

    logger.info(f"\nAll elements dumped to: all_elements.txt")
    logger.info(f"Screenshot saved to: screenshot_mainpage.png")

    # Try clicking search input to see if more options appear
    logger.info("\n" + "=" * 70)
    logger.info("Clicking search input to check for additional UI...")
    logger.info("=" * 70)

    try:
        search_input = await page.find('textarea', best_match=True, timeout=5)
        if search_input:
            await search_input.click()
            await asyncio.sleep(2)

            logger.info("Taking screenshot 2: After clicking search")
            await page.save_screenshot('screenshot_search_active.png')

            # Search again for new elements
            elements_after = await page.evaluate(js_code)
            new_count = len(elements_after) - len(elements)

            if new_count > 0:
                logger.info(f"\n{new_count} NEW elements appeared after clicking search!")

                with open('elements_after_click.txt', 'w') as f:
                    for el in elements_after[len(elements):]:
                        f.write(f"\n{'='*70}\n")
                        f.write(f"[{el['index']}] {el['tag']}\n")
                        f.write(f"Text: {el['text']}\n")
                        f.write(f"data-testid: {el['testId']}\n")
                        f.write(f"aria-label: {el['ariaLabel']}\n")
                        f.write(f"role: {el['role']}\n")
                        f.write(f"class: {el['className']}\n")

                logger.info("New elements dumped to: elements_after_click.txt")

    except Exception as e:
        logger.warning(f"Could not click search: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("Discovery complete! Check the following files:")
    logger.info("  - screenshot_mainpage.png")
    logger.info("  - screenshot_search_active.png")
    logger.info("  - all_elements.txt")
    logger.info("  - elements_after_click.txt")
    logger.info("=" * 70)

    # Keep browser open
    logger.info("\nBrowser will stay open. Press Ctrl+C to close.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Closing...")
        browser.stop()


if __name__ == '__main__':
    asyncio.run(main())
