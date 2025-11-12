"""
Simplified diagnostic script for new chat button after search
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
from src.utils.cookies import load_cookies
from src.browser.auth import set_cookies, verify_authentication
from src.browser.navigation import navigate_to_new_chat
from src.search.executor import perform_search
from src.config import NEW_CHAT_CONFIG


async def diagnose():
    print("\n=== NEW CHAT DIAGNOSTIC (Simplified) ===\n")

    browser = None
    try:
        # Launch and authenticate
        print("1. Launching browser and authenticating...")
        browser = await uc.start(headless=False)
        page = browser.main_tab
        cookies = load_cookies()
        await set_cookies(page, cookies)
        await page.get("https://www.perplexity.ai")
        await asyncio.sleep(3)

        is_auth = await verify_authentication(page)
        print(f"   Authentication: {'✅ PASS' if is_auth else '❌ FAIL'}\n")

        if not is_auth:
            return

        # Perform search
        print("2. Performing test search...")
        url_before = page.url
        await perform_search(page, "What is GEO?")
        await asyncio.sleep(5)
        url_after = page.url
        print(f"   Before: {url_before}")
        print(f"   After:  {url_after}")
        print(f"   URL changed: {url_before != url_after}\n")

        # Check if new chat button exists
        print("3. Looking for new chat button...")
        selectors = NEW_CHAT_CONFIG.get('selectors', [])

        # Build JavaScript with selectors embedded (nodriver doesn't pass params like playwright)
        import json
        selectors_json = json.dumps(selectors)

        button_info = await page.evaluate(f"""
            (() => {{
                const selectors = {selectors_json};
                for (const selector of selectors) {{
                    const btn = document.querySelector(selector);
                    if (btn) {{
                        const rect = btn.getBoundingClientRect();
                        const style = window.getComputedStyle(btn);
                        return {{
                            found: true,
                            selector: selector,
                            visible: style.display !== 'none' && style.visibility !== 'hidden',
                            inViewport: rect.top >= 0 && rect.width > 0 && rect.height > 0,
                            dimensions: `${{rect.width}}x${{rect.height}}`,
                            text: btn.innerText || btn.textContent || '',
                            ariaLabel: btn.getAttribute('aria-label')
                        }};
                    }}
                }}
                return {{found: false}};
            }})()
        """)

        # Handle nodriver's evaluate return format (sometimes list, sometimes dict)
        if isinstance(button_info, list) and len(button_info) > 0:
            button_info = button_info[0] if isinstance(button_info[0], dict) else {'found': False}
        elif not isinstance(button_info, dict):
            button_info = {'found': False}

        if button_info.get('found'):
            print(f"   ✅ FOUND: {button_info.get('selector')}")
            print(f"   - Visible: {button_info.get('visible')}")
            print(f"   - In viewport: {button_info.get('inViewport')}")
            print(f"   - Size: {button_info.get('dimensions')}")
            print(f"   - Text: '{button_info.get('text')}'")
            print(f"   - Aria-label: '{button_info.get('ariaLabel')}'")
        else:
            print(f"   ❌ NOT FOUND")
            print(f"   Tried {len(selectors)} selectors:")
            for s in selectors:
                print(f"     - {s}")

            # Show what buttons exist
            print("\n   Visible buttons on page:")
            buttons = await page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    let found = [];
                    for (const btn of buttons) {
                        const rect = btn.getBoundingClientRect();
                        const style = window.getComputedStyle(btn);
                        if (style.display !== 'none' && rect.width > 0) {
                            found.push({
                                text: (btn.innerText || '').substring(0, 40),
                                aria: btn.getAttribute('aria-label'),
                                testid: btn.getAttribute('data-testid')
                            });
                            if (found.length >= 5) break;
                        }
                    }
                    return found;
                }
            """)
            for i, btn in enumerate(buttons, 1):
                print(f"     {i}. Text: '{btn.get('text')}' | Aria: '{btn.get('aria')}' | TestID: '{btn.get('testid')}'")

            print("\n   ❌ DIAGNOSIS: Button not found after search - selectors may be outdated")
            return

        # Try to navigate
        print("\n4. Attempting navigation to new chat...")
        prev_url = page.url
        nav_result = await navigate_to_new_chat(page, verify=True, previous_url=prev_url)
        new_url = page.url

        print(f"   Navigation result: {'✅ SUCCESS' if nav_result else '❌ FAILED'}")
        print(f"   URL before: {prev_url}")
        print(f"   URL after:  {new_url}")
        print(f"   URL changed: {prev_url != new_url}")

        # Check page state
        print("\n5. Checking page state...")
        page_state = await page.evaluate("""
            () => {
                const oldContent = document.querySelectorAll('[data-testid*="answer"]').length;
                const searchInput = document.querySelector('[contenteditable="true"]') ||
                                   document.querySelector('textarea[placeholder*="Ask"]');
                const inputValue = searchInput ?
                    (searchInput.value || searchInput.innerText || '') : '';

                return {
                    oldContentCount: oldContent,
                    searchInputFound: searchInput !== null,
                    searchInputEmpty: inputValue.trim() === ''
                };
            }
        """)

        print(f"   Old content elements: {page_state.get('oldContentCount')}")
        print(f"   Search input found: {page_state.get('searchInputFound')}")
        print(f"   Search input empty: {page_state.get('searchInputEmpty')}")

        # Final diagnosis
        print("\n" + "="*50)
        print("DIAGNOSIS SUMMARY")
        print("="*50)

        if not button_info.get('found'):
            print("\n❌ ROOT CAUSE: New chat button not found after search")
            print("   FIX: Update selectors in NEW_CHAT_CONFIG")
        elif not nav_result:
            print("\n❌ ROOT CAUSE: Navigation verification failed")
            if prev_url == new_url:
                print("   DETAIL: URL did not change (click had no effect)")
                print("   FIX: Button may be non-functional or wrong element")
            elif page_state.get('oldContentCount') > 0:
                print("   DETAIL: Old content still present")
                print("   FIX: Increase verification timeout or relax checks")
            else:
                print("   DETAIL: Unknown verification failure")
                print("   FIX: Check verification logic in navigation.py")
        else:
            print("\n✅ Everything working correctly!")

        print("\n" + "="*50)
        print("Press Ctrl+C to close browser...")
        print("="*50 + "\n")

        # Keep open
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing...")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            browser.stop()


if __name__ == "__main__":
    asyncio.run(diagnose())
