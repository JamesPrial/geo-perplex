"""
Targeted script to find the AI model selector in Perplexity Pro
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.utils.cookies import load_cookies

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Find the model selector."""

    logger.info("Setting up browser...")
    cookies = load_cookies()
    browser = await launch_browser()
    page = await browser.get('about:blank')
    await set_cookies(page, cookies)

    logger.info("Navigating to Perplexity...")
    await page.get('https://www.perplexity.ai', new_tab=False)
    await asyncio.sleep(4)

    is_authenticated = await verify_authentication(page)
    if not is_authenticated:
        logger.error("Auth failed!")
        return

    logger.info("✓ Authenticated\n")

    # Step 1: Main page
    logger.info("Step 1: Main page screenshot")
    await page.save_screenshot('step1_main.png')

    # Step 2: Click search input
    logger.info("Step 2: Clicking search input...")
    try:
        search = await page.find('textarea', timeout=5)
        if search:
            await search.click()
            await asyncio.sleep(2)
            await page.save_screenshot('step2_search_focused.png')
            logger.info("✓ Search focused, screenshot saved")
    except Exception as e:
        logger.error(f"✗ Could not click search: {e}")

    # Step 3: Look for buttons near search with model-related attributes
    logger.info("\nStep 3: Searching for model-related buttons...")

    js_find_buttons = """
    () => {
        const buttons = [];

        // Get all buttons and button-like elements
        const elements = document.querySelectorAll('button, [role="button"], [role="combobox"]');

        elements.forEach((el, idx) => {
            const rect = el.getBoundingClientRect();

            // Only visible elements
            if (rect.width > 0 && rect.height > 0) {
                const text = (el.textContent || '').trim();
                const ariaLabel = el.getAttribute('aria-label') || '';
                const testId = el.getAttribute('data-testid') || '';
                const title = el.getAttribute('title') || '';

                // Check if it might be model-related
                const allText = (text + ariaLabel + testId + title).toLowerCase();
                const isModelRelated = allText.includes('model') ||
                                      allText.includes('gpt') ||
                                      allText.includes('claude') ||
                                      allText.includes('sonar') ||
                                      allText.includes('select') ||
                                      allText.includes('pro') ||
                                      allText.includes('focus');

                buttons.push({
                    idx: idx,
                    tag: el.tagName,
                    text: text.substring(0, 50),
                    ariaLabel: ariaLabel,
                    testId: testId,
                    title: title,
                    className: el.className,
                    isNearSearch: rect.top < 600,  // Near search area
                    isModelRelated: isModelRelated,
                    pos: `(${Math.round(rect.left)}, ${Math.round(rect.top)})`
                });
            }
        });

        return buttons;
    }
    """

    try:
        buttons = await page.evaluate(js_find_buttons)

        if buttons:
            logger.info(f"Found {len(buttons)} buttons total\n")

            # Show model-related ones first
            model_buttons = [b for b in buttons if b['isModelRelated']]
            if model_buttons:
                logger.info("🎯 MODEL-RELATED BUTTONS:")
                for b in model_buttons:
                    logger.info(f"\n  [{b['idx']}] {b['tag']}")
                    if b['text']:
                        logger.info(f"    Text: {b['text']}")
                    if b['ariaLabel']:
                        logger.info(f"    aria-label: {b['ariaLabel']}")
                    if b['testId']:
                        logger.info(f"    data-testid: {b['testId']}")
                    if b['title']:
                        logger.info(f"    title: {b['title']}")
                    logger.info(f"    Position: {b['pos']}")

            # Show buttons near search area
            near_search = [b for b in buttons if b['isNearSearch'] and not b['isModelRelated']]
            if near_search:
                logger.info("\n📍 BUTTONS NEAR SEARCH AREA:")
                for b in near_search[:10]:  # First 10
                    logger.info(f"\n  [{b['idx']}] {b['text'][:30] if b['text'] else '(no text)'}")
                    if b['testId']:
                        logger.info(f"    data-testid: {b['testId']}")
                    if b['ariaLabel']:
                        logger.info(f"    aria-label: {b['ariaLabel']}")

            # Save all to file
            with open('all_buttons.txt', 'w') as f:
                for b in buttons:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{b['idx']}] {b['tag']}\n")
                    f.write(f"Text: {b['text']}\n")
                    f.write(f"aria-label: {b['ariaLabel']}\n")
                    f.write(f"data-testid: {b['testId']}\n")
                    f.write(f"title: {b['title']}\n")
                    f.write(f"className: {b['className']}\n")
                    f.write(f"Position: {b['pos']}\n")
                    f.write(f"Near search: {b['isNearSearch']}\n")
                    f.write(f"Model-related: {b['isModelRelated']}\n")

            logger.info(f"\n✓ All buttons saved to: all_buttons.txt")

    except Exception as e:
        logger.error(f"Error finding buttons: {e}")

    # Step 4: Try to find the selector by looking at SVG icons or specific areas
    logger.info("\nStep 4: Checking for icons/selectors in search controls...")

    js_find_icons = """
    () => {
        const icons = [];
        const searchArea = document.querySelector('textarea')?.closest('div[class*="search"], div[class*="input"], form');

        if (searchArea) {
            const svgs = searchArea.querySelectorAll('svg, button');
            svgs.forEach((el, idx) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0) {
                    const parent = el.closest('button') || el.parentElement;
                    icons.push({
                        idx: idx,
                        type: el.tagName,
                        parentTag: parent?.tagName,
                        testId: parent?.getAttribute('data-testid') || '',
                        ariaLabel: parent?.getAttribute('aria-label') || '',
                        title: parent?.getAttribute('title') || '',
                        className: parent?.className || ''
                    });
                }
            });
        }

        return icons;
    }
    """

    try:
        icons = await page.evaluate(js_find_icons)
        if icons:
            logger.info(f"Found {len(icons)} icons/buttons in search area:")
            for icon in icons:
                logger.info(f"\n  [{icon['idx']}] {icon['type']} in {icon['parentTag']}")
                if icon['testId']:
                    logger.info(f"    data-testid: {icon['testId']}")
                if icon['ariaLabel']:
                    logger.info(f"    aria-label: {icon['ariaLabel']}")
                if icon['title']:
                    logger.info(f"    title: {icon['title']}")
    except Exception as e:
        logger.error(f"Error finding icons: {e}")

    logger.info("\n" + "="*60)
    logger.info("DISCOVERY COMPLETE!")
    logger.info("="*60)
    logger.info("Files created:")
    logger.info("  - step1_main.png")
    logger.info("  - step2_search_focused.png")
    logger.info("  - all_buttons.txt")
    logger.info("\nBrowser will stay open. Press Ctrl+C to close.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Closing...")
        browser.stop()


if __name__ == '__main__':
    asyncio.run(main())
