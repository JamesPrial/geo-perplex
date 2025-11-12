"""
Investigation script to find and inspect the new chat button (+ sign) on Perplexity.ai
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
from src.utils.cookies import load_cookies
from src.browser.auth import set_cookies


async def inspect_new_chat_button():
    """Find and inspect the new chat button on Perplexity."""
    print("🔍 Starting investigation of new chat button...")

    # Launch browser (must be headed for Perplexity)
    browser = await uc.start(headless=False)
    page = await browser.get("about:blank")

    try:
        # Load and set cookies
        print("🍪 Loading authentication cookies...")
        cookies = load_cookies()
        await set_cookies(page, cookies)

        # Navigate to Perplexity
        print("🌐 Navigating to Perplexity.ai...")
        await page.get("https://www.perplexity.ai")
        await asyncio.sleep(3)  # Wait for page to load

        print("\n" + "="*80)
        print("Looking for new chat button (+ sign in top left)...")
        print("="*80 + "\n")

        # Strategy 1: Look for button with + text
        print("Strategy 1: Searching for buttons with '+' text...")
        buttons = await page.select_all("button")
        for i, btn in enumerate(buttons):
            text = btn.text_all.strip()
            if '+' in text or 'new' in text.lower() or 'chat' in text.lower():
                print(f"\n  Found button #{i}:")
                print(f"    Text: '{text}'")
                print(f"    HTML: {await btn.get_html()[:200]}...")

                # Get attributes
                attrs = {}
                for attr in ['data-testid', 'aria-label', 'class', 'id', 'type']:
                    try:
                        val = await btn.get_attribute(attr)
                        if val:
                            attrs[attr] = val
                    except:
                        pass
                if attrs:
                    print(f"    Attributes: {attrs}")

        # Strategy 2: Look for common new chat button patterns
        print("\n\nStrategy 2: Trying common selector patterns...")
        patterns = [
            'button[aria-label*="new"]',
            'button[aria-label*="New"]',
            'button[aria-label*="chat"]',
            'button[aria-label*="Chat"]',
            'button[data-testid*="new"]',
            'button[data-testid*="chat"]',
            '[data-testid*="new-chat"]',
            '[data-testid*="new-thread"]',
            'button svg + span',  # Button with icon + text
            'button:has(svg)',  # Buttons containing SVG icons
        ]

        for pattern in patterns:
            try:
                elements = await page.select_all(pattern)
                if elements:
                    print(f"\n  Pattern '{pattern}' found {len(elements)} elements:")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.text_all.strip()
                        html = await elem.get_html()
                        print(f"    [{i}] Text: '{text}'")
                        print(f"        HTML: {html[:150]}...")
            except Exception as e:
                print(f"  Pattern '{pattern}' error: {e}")

        # Strategy 3: Get all elements in top-left area
        print("\n\nStrategy 3: Inspecting top-left area of page...")
        print("  (Looking for elements in first 200px of width/height)")

        # Use JavaScript to find elements in top-left corner
        js_code = """
        () => {
            const elements = [];
            const all = document.querySelectorAll('*');
            all.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.left < 200 && rect.top < 200 && rect.width > 0 && rect.height > 0) {
                    elements.push({
                        tag: el.tagName,
                        text: el.textContent?.substring(0, 50),
                        class: el.className,
                        id: el.id,
                        testid: el.getAttribute('data-testid'),
                        ariaLabel: el.getAttribute('aria-label'),
                        left: Math.round(rect.left),
                        top: Math.round(rect.top),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });
            return elements;
        }
        """

        top_left_elements = await page.evaluate(js_code)

        # Filter for likely button candidates
        print("\n  Interactive elements in top-left:")
        for elem in top_left_elements:
            if elem['tag'] in ['BUTTON', 'A'] or 'button' in str(elem['class']).lower():
                print(f"\n    {elem['tag']} at ({elem['left']}px, {elem['top']}px)")
                print(f"      Size: {elem['width']}x{elem['height']}px")
                if elem['text']:
                    print(f"      Text: '{elem['text']}'")
                if elem['class']:
                    print(f"      Class: '{elem['class']}'")
                if elem['testid']:
                    print(f"      data-testid: '{elem['testid']}'")
                if elem['ariaLabel']:
                    print(f"      aria-label: '{elem['ariaLabel']}'")

        print("\n" + "="*80)
        print("✅ Investigation complete!")
        print("="*80)
        print("\nThe browser will stay open so you can manually inspect with DevTools.")
        print("Press Ctrl+C when done to close.")

        # Keep browser open for manual inspection
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 Closing browser...")
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.stop()


if __name__ == "__main__":
    asyncio.run(inspect_new_chat_button())
