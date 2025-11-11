"""
Click the model selector (circuit icon) and capture the model options
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.utils.cookies import load_cookies
from src.browser.interactions import human_delay

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Find and click the model selector button."""

    logger.info("Setting up...")
    cookies = load_cookies()
    browser = await launch_browser()
    page = await browser.get('about:blank')
    await set_cookies(page, cookies)

    logger.info("Navigating...")
    await page.get('https://www.perplexity.ai', new_tab=False)
    await asyncio.sleep(4)

    if not await verify_authentication(page):
        logger.error("Auth failed!")
        return

    logger.info("✓ Authenticated\n")

    # Take screenshot before
    await page.save_screenshot('before_click.png')
    logger.info("📸 before_click.png saved")

    # Find all buttons in the search container area
    logger.info("\n🔍 Finding buttons in search area...")

    js_find_search_buttons = """
    () => {
        // Find the search textarea first
        const textarea = document.querySelector('textarea');
        if (!textarea) return null;

        // Get the parent container (likely contains the textarea and buttons)
        const container = textarea.closest('div[class*="search"], form, div[role="search"]') ||
                         textarea.parentElement.parentElement;

        if (!container) return null;

        // Find all buttons in this container
        const buttons = Array.from(container.querySelectorAll('button, [role="button"]'));

        return buttons.map((btn, idx) => {
            const rect = btn.getBoundingClientRect();

            // Get all SVG paths to identify icons
            const svgs = Array.from(btn.querySelectorAll('svg'));
            const paths = Array.from(btn.querySelectorAll('svg path')).map(p => p.getAttribute('d') || '');

            return {
                idx: idx,
                visible: rect.width > 0 && rect.height > 0,
                position: {
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    top: Math.round(rect.top),
                    bottom: Math.round(rect.bottom)
                },
                testId: btn.getAttribute('data-testid') || '',
                ariaLabel: btn.getAttribute('aria-label') || '',
                title: btn.getAttribute('title') || '',
                hasSvg: svgs.length > 0,
                svgCount: svgs.length,
                pathCount: paths.length,
                // Store a signature of the icon (first path snippet)
                iconSignature: paths[0] ? paths[0].substring(0, 50) : ''
            };
        }).filter(b => b.visible);
    }
    """

    buttons = await page.evaluate(js_find_search_buttons)

    if not buttons:
        logger.error("❌ No buttons found in search area!")
        return

    logger.info(f"Found {len(buttons)} buttons in search container:\n")

    # Show all buttons
    for b in buttons:
        logger.info(f"  Button [{b['idx']}]:")
        logger.info(f"    Position: left={b['position']['left']}, right={b['position']['right']}")
        if b['testId']:
            logger.info(f"    data-testid: {b['testId']}")
        if b['ariaLabel']:
            logger.info(f"    aria-label: {b['ariaLabel']}")
        if b['title']:
            logger.info(f"    title: {b['title']}")
        logger.info(f"    Has SVG: {b['hasSvg']} ({b['svgCount']} svg, {b['pathCount']} paths)")
        if b['iconSignature']:
            logger.info(f"    Icon signature: {b['iconSignature'][:40]}...")
        logger.info("")

    # The buttons on the right side of the search box
    # User said: globe (sources), circuit (models), then 3 more
    # So we want the SECOND button from the right side buttons

    # Filter to buttons on the right side (assuming right > 800px or so)
    right_side_buttons = [b for b in buttons if b['position']['left'] > 600]
    right_side_buttons.sort(key=lambda b: b['position']['left'])  # Sort left to right

    if len(right_side_buttons) < 2:
        logger.error(f"❌ Found only {len(right_side_buttons)} buttons on right side")
        logger.info("All buttons:")
        for b in buttons:
            logger.info(f"  idx={b['idx']}, left={b['position']['left']}")
        return

    # Try to click the second button (circuit icon - models)
    model_button_idx = right_side_buttons[1]['idx']  # 0=globe, 1=circuit

    logger.info(f"🎯 Targeting button [{model_button_idx}] (2nd from left on right side)")
    logger.info(f"   This should be the circuit icon (model selector)")
    logger.info("")

    # Click it using JavaScript
    js_click = f"""
    () => {{
        const textarea = document.querySelector('textarea');
        const container = textarea.closest('div[class*="search"], form, div[role="search"]') ||
                         textarea.parentElement.parentElement;
        const buttons = Array.from(container.querySelectorAll('button, [role="button"]'));
        const targetButton = buttons[{model_button_idx}];

        if (targetButton) {{
            targetButton.click();
            return true;
        }}
        return false;
    }}
    """

    clicked = await page.evaluate(js_click)

    if clicked:
        logger.info("✓ Clicked model selector button!")
        await asyncio.sleep(2)  # Wait for dropdown/modal to appear

        # Take screenshot after click
        await page.save_screenshot('after_click_models.png')
        logger.info("📸 after_click_models.png saved")

        # Now find the model options
        logger.info("\n🔍 Searching for model options...")

        js_find_models = """
        () => {
            const results = [];

            // Look for common dropdown/menu containers
            const containers = document.querySelectorAll('[role="menu"], [role="listbox"], [role="dialog"], [class*="dropdown"], [class*="menu"], [class*="modal"], [class*="popup"]');

            containers.forEach(container => {
                // Only recently appeared elements (might have just rendered)
                const rect = container.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    // Find clickable items inside
                    const items = container.querySelectorAll('[role="menuitem"], [role="option"], button, a, li, div[class*="option"]');

                    items.forEach(item => {
                        const text = item.textContent?.trim() || '';
                        const itemRect = item.getBoundingClientRect();

                        if (text && itemRect.width > 0 && text.length < 100) {
                            results.push({
                                text: text,
                                tag: item.tagName,
                                role: item.getAttribute('role') || '',
                                testId: item.getAttribute('data-testid') || '',
                                ariaLabel: item.getAttribute('aria-label') || '',
                                className: item.className
                            });
                        }
                    });
                }
            });

            return results;
        }
        """

        models = await page.evaluate(js_find_models)

        if models:
            logger.info(f"✅ Found {len(models)} model options:\n")

            for m in models:
                logger.info(f"  • {m['text']}")
                if m['testId']:
                    logger.info(f"    data-testid: {m['testId']}")
                if m['ariaLabel']:
                    logger.info(f"    aria-label: {m['ariaLabel']}")
                logger.info(f"    tag: {m['tag']}, role: {m['role']}")
                logger.info("")

            # Save to file
            with open('model_options.txt', 'w') as f:
                f.write("Model Options Found:\n")
                f.write("=" * 60 + "\n\n")
                for m in models:
                    f.write(f"Text: {m['text']}\n")
                    f.write(f"Tag: {m['tag']}\n")
                    f.write(f"Role: {m['role']}\n")
                    f.write(f"data-testid: {m['testId']}\n")
                    f.write(f"aria-label: {m['ariaLabel']}\n")
                    f.write(f"className: {m['className']}\n")
                    f.write("\n" + "-" * 60 + "\n\n")

            logger.info("✅ Model options saved to: model_options.txt")

        else:
            logger.warning("⚠️  No model options found - modal might not have opened")

    else:
        logger.error("❌ Failed to click button")

    logger.info("\n" + "=" * 60)
    logger.info("FILES CREATED:")
    logger.info("  - before_click.png")
    logger.info("  - after_click_models.png")
    logger.info("  - model_options.txt")
    logger.info("=" * 60)

    logger.info("\nBrowser staying open. Press Ctrl+C to close.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Closing...")
        browser.stop()


if __name__ == '__main__':
    asyncio.run(main())
