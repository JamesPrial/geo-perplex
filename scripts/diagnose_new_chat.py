"""
Diagnostic script to investigate the new chat button behavior after querying

This script will:
1. Perform a search on Perplexity
2. Attempt to click the new chat button
3. Log detailed diagnostic information about what happens
4. Check URL changes, DOM state, and element visibility
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
from src.utils.cookies import load_cookies
from src.browser.auth import set_cookies, verify_authentication
from src.browser.interactions import human_delay, find_interactive_element
from src.browser.navigation import navigate_to_new_chat
from src.search.executor import perform_search
from src.config import NEW_CHAT_CONFIG

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def diagnose_new_chat_after_search():
    """
    Diagnose new chat button behavior after performing a search.
    """
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSTIC SCRIPT: New Chat After Search")
    print("=" * 80 + "\n")

    browser = None
    try:
        # Step 1: Launch browser
        print("1. Launching browser...")
        browser = await uc.start(headless=False)
        page = browser.main_tab

        # Step 2: Load and set cookies
        print("\n2. Loading authentication cookies...")
        cookies = load_cookies()
        await set_cookies(page, cookies)

        # Step 3: Navigate to Perplexity
        print("\n3. Navigating to Perplexity.ai...")
        await page.get("https://www.perplexity.ai")
        await asyncio.sleep(3)

        # Step 4: Verify authentication
        print("\n4. Verifying authentication...")
        is_auth = await verify_authentication(page)
        print(f"   Authentication status: {'✅ Authenticated' if is_auth else '❌ Not authenticated'}")

        if not is_auth:
            print("   ⚠️  Cannot proceed without authentication")
            return

        # Step 5: Perform a search
        print("\n5. Performing test search...")
        test_query = "What is GEO?"
        print(f"   Query: {test_query}")

        url_before_search = page.url
        print(f"   URL before search: {url_before_search}")

        await perform_search(page, test_query)
        await asyncio.sleep(5)  # Wait for search to complete

        url_after_search = page.url
        print(f"   URL after search: {url_after_search}")
        print(f"   URL changed: {url_before_search != url_after_search}")

        # Step 6: Check for search results
        print("\n6. Checking for search results in DOM...")
        result_check = await page.evaluate("""
            (() => {
                const selectors = [
                    '[data-testid*="answer"]',
                    '[data-testid*="source"]',
                    '[class*="answer"]',
                    '[class*="response"]'
                ];

                let found = [];
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        found.push({selector: selector, count: elements.length});
                    }
                }

                return {
                    hasResults: found.length > 0,
                    foundElements: found,
                    bodyTextLength: document.body.innerText.length
                };
            })()
        """)
        print(f"   Has search results: {result_check.get('hasResults')}")
        print(f"   Body text length: {result_check.get('bodyTextLength')} chars")
        if result_check.get('foundElements'):
            print(f"   Found result elements:")
            for elem in result_check['foundElements']:
                print(f"     - {elem['selector']}: {elem['count']} elements")

        # Step 7: Check for new chat button visibility
        print("\n7. Checking new chat button visibility...")
        selectors = NEW_CHAT_CONFIG.get('selectors', [])
        print(f"   Testing {len(selectors)} selectors:")

        button_found = False
        button_selector = None
        for selector in selectors:
            try:
                button = await find_interactive_element(
                    page,
                    [selector],
                    timeout=2.0
                )
                if button:
                    print(f"   ✅ Found with selector: {selector}")
                    button_found = True
                    button_selector = selector

                    # Check button properties
                    button_info = await page.evaluate("""
                        (selector) => {
                            const el = document.querySelector(selector);
                            if (!el) return null;

                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);

                            return {
                                visible: style.display !== 'none' && style.visibility !== 'hidden',
                                enabled: !el.disabled && el.getAttribute('aria-disabled') !== 'true',
                                inViewport: rect.top >= 0 && rect.left >= 0,
                                dimensions: {width: rect.width, height: rect.height},
                                text: el.innerText || el.textContent,
                                ariaLabel: el.getAttribute('aria-label')
                            };
                        }
                    """, selector)

                    if button_info:
                        print(f"     - Visible: {button_info.get('visible')}")
                        print(f"     - Enabled: {button_info.get('enabled')}")
                        print(f"     - In viewport: {button_info.get('inViewport')}")
                        print(f"     - Dimensions: {button_info.get('dimensions')}")
                        print(f"     - Text: '{button_info.get('text')}'")
                        print(f"     - Aria-label: '{button_info.get('ariaLabel')}'")

                    break
                else:
                    print(f"   ❌ Not found: {selector}")
            except Exception as e:
                print(f"   ❌ Error with {selector}: {e}")

        if not button_found:
            print("\n   ⚠️  NEW CHAT BUTTON NOT FOUND!")
            print("   This is the likely cause of the issue.")
            print("\n   Let's check what buttons ARE visible:")

            visible_buttons = await page.evaluate("""
                (() => {
                    const buttons = document.querySelectorAll('button');
                    let visible = [];

                    for (const btn of buttons) {
                        const rect = btn.getBoundingClientRect();
                        const style = window.getComputedStyle(btn);

                        if (style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            rect.width > 0 && rect.height > 0) {
                            visible.push({
                                text: (btn.innerText || btn.textContent || '').trim().substring(0, 50),
                                ariaLabel: btn.getAttribute('aria-label'),
                                testId: btn.getAttribute('data-testid'),
                                classes: btn.className
                            });
                        }
                    }

                    return visible.slice(0, 10);  // First 10 visible buttons
                })()
            """)

            print(f"\n   Found {len(visible_buttons)} visible buttons:")
            for i, btn in enumerate(visible_buttons, 1):
                print(f"   {i}. Text: '{btn.get('text')}'")
                print(f"      Aria-label: '{btn.get('ariaLabel')}'")
                print(f"      Test ID: '{btn.get('testId')}'")
                print(f"      Classes: '{btn.get('classes')[:80]}'...")
                print()

            return

        # Step 8: Attempt to click new chat button
        print("\n8. Attempting to navigate to new chat...")
        url_before_nav = page.url
        print(f"   URL before navigation: {url_before_nav}")

        nav_success = await navigate_to_new_chat(
            page,
            verify=True,
            previous_url=url_before_nav
        )

        url_after_nav = page.url
        print(f"\n   Navigation result: {'✅ SUCCESS' if nav_success else '❌ FAILED'}")
        print(f"   URL after navigation: {url_after_nav}")
        print(f"   URL changed: {url_before_nav != url_after_nav}")

        # Step 9: Check DOM state after navigation
        print("\n9. Checking DOM state after navigation...")
        await asyncio.sleep(2)  # Wait for DOM to update

        post_nav_check = await page.evaluate("""
            (() => {
                const oldContentSelectors = [
                    '[data-testid*="answer"]',
                    '[data-testid*="source"]',
                    '[class*="answer"]',
                    '[class*="response"]'
                ];

                let oldContentFound = [];
                for (const selector of oldContentSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        oldContentFound.push({selector: selector, count: elements.length});
                    }
                }

                const searchInput = document.querySelector('[contenteditable="true"]') ||
                                   document.querySelector('textarea[placeholder*="Ask"]');
                const inputValue = searchInput ?
                    (searchInput.value || searchInput.innerText || searchInput.textContent || '') : null;

                return {
                    oldContentStillPresent: oldContentFound.length > 0,
                    oldContentElements: oldContentFound,
                    searchInputFound: searchInput !== null,
                    searchInputEmpty: inputValue !== null ? inputValue.trim() === '' : null,
                    bodyText: document.body.innerText.substring(0, 500)
                };
            })()
        """)

        print(f"   Old content still present: {post_nav_check.get('oldContentStillPresent')}")
        if post_nav_check.get('oldContentElements'):
            print(f"   Old content elements found:")
            for elem in post_nav_check['oldContentElements']:
                print(f"     - {elem['selector']}: {elem['count']} elements")

        print(f"   Search input found: {post_nav_check.get('searchInputFound')}")
        print(f"   Search input empty: {post_nav_check.get('searchInputEmpty')}")
        print(f"\n   Body text preview (first 500 chars):")
        print(f"   {post_nav_check.get('bodyText')}")

        # Step 10: Final assessment
        print("\n" + "=" * 80)
        print("📋 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print(f"\n1. New chat button found: {button_found}")
        if button_found:
            print(f"   Selector used: {button_selector}")
        print(f"\n2. Navigation succeeded: {nav_success}")
        print(f"\n3. URL changed after nav: {url_before_nav != url_after_nav}")
        print(f"   Before: {url_before_nav}")
        print(f"   After:  {url_after_nav}")
        print(f"\n4. Old content removed: {not post_nav_check.get('oldContentStillPresent')}")
        print(f"\n5. Search input ready: {post_nav_check.get('searchInputFound') and post_nav_check.get('searchInputEmpty')}")

        # Identify the issue
        print("\n" + "=" * 80)
        print("🔍 ROOT CAUSE ANALYSIS")
        print("=" * 80)

        if not button_found:
            print("\n❌ ISSUE: New chat button not found after search")
            print("   Possible causes:")
            print("   - Button selector changed in Perplexity UI")
            print("   - Button is hidden/disabled after search")
            print("   - Button requires scrolling to become visible")
        elif not nav_success:
            print("\n❌ ISSUE: Navigation verification failed")
            print("   Possible causes:")
            print("   - Verification checks too strict")
            print("   - Old content not being removed from DOM")
            print("   - URL not changing as expected")
        elif url_before_nav == url_after_nav:
            print("\n❌ ISSUE: URL did not change after clicking new chat button")
            print("   This indicates the button click had no effect")
            print("   Possible causes:")
            print("   - Button click not actually executing")
            print("   - JavaScript preventing navigation")
            print("   - Button is not the correct element")
        elif post_nav_check.get('oldContentStillPresent'):
            print("\n⚠️  ISSUE: Old search results still present in DOM")
            print("   This may be expected - Perplexity might keep old DOM")
            print("   But verification is failing because of this")
        else:
            print("\n✅ Everything appears to be working correctly!")
            print("   If you're experiencing issues, they may be intermittent")

        print("\n" + "=" * 80)
        print("Browser will stay open for manual inspection.")
        print("Press Ctrl+C when done.")
        print("=" * 80 + "\n")

        # Keep browser open
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\nClosing browser...")

    except Exception as e:
        logger.error(f"Diagnostic error: {e}", exc_info=True)
        print(f"\n❌ Error during diagnostic: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            browser.stop()


if __name__ == "__main__":
    asyncio.run(diagnose_new_chat_after_search())
