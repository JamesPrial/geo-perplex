#!/usr/bin/env python3
"""
Investigation script to locate and test the collapsible sources button.

This script:
1. Performs a search on Perplexity.ai
2. Waits for results to complete
3. Tries multiple strategies to find the "x sources" button
4. Tests clicking and verifying expansion
5. Documents all findings
"""

import asyncio
import sys
import os
from pathlib import Path
import hashlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG, SELECTORS, TIMEOUTS


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(title.upper())
    print("="*80)


async def wait_for_content_stability(page, max_wait=30, check_interval=0.5):
    """Wait for page content to stabilize (answer generation complete)."""
    print(f"\nWaiting for content stability (max {max_wait}s, checking every {check_interval}s)...")

    stable_count = 0
    required_stable_checks = 3
    last_hash = None
    start_time = asyncio.get_event_loop().time()

    while (asyncio.get_event_loop().time() - start_time) < max_wait:
        try:
            # Get main content
            main = await page.select('main')
            if main:
                content = main.text_all
                current_hash = hashlib.md5(content.encode()).hexdigest()

                if current_hash == last_hash:
                    stable_count += 1
                    if stable_count >= required_stable_checks:
                        print(f"✓ Content stable after {asyncio.get_event_loop().time() - start_time:.1f}s")
                        return True
                else:
                    stable_count = 0
                    last_hash = current_hash
        except Exception as e:
            print(f"  Warning: Error checking stability: {e}")

        await asyncio.sleep(check_interval)

    print(f"⚠ Content did not stabilize within {max_wait}s, proceeding anyway...")
    return False


async def investigate_sources_button(query="What are the benefits of meditation?"):
    """Investigate how to find and click the collapsible sources button."""

    print_section("PERPLEXITY COLLAPSIBLE SOURCES BUTTON INVESTIGATION")
    print(f"Query: {query}\n")

    # Load cookies
    print("1. Loading authentication cookies...")
    cookies = load_cookies()
    print(f"✓ Loaded {len(cookies)} cookies from auth.json")

    # Start browser
    print("\n2. Starting browser...")
    browser = await uc.start(
        browser_args=BROWSER_CONFIG['args'],
        headless=False
    )

    page = await browser.get("about:blank")

    # Set cookies
    print("\n3. Setting cookies...")
    for cookie in cookies:
        try:
            await page.send(cdp.network.set_cookie(
                name=cookie['name'],
                value=cookie['value'],
                domain=cookie.get('domain', '.perplexity.ai'),
                path=cookie.get('path', '/'),
                secure=cookie.get('secure', True),
                http_only=cookie.get('httpOnly', False),
                same_site=cdp.network.CookieSameSite(cookie.get('sameSite', 'None')) if cookie.get('sameSite') else None,
                expires=cdp.network.TimeSinceEpoch(cookie['expires']) if cookie.get('expires') and cookie['expires'] > 0 else None
            ))
        except Exception as e:
            print(f"   Warning: Could not set cookie {cookie['name']}: {e}")

    # Navigate to Perplexity
    print("\n4. Navigating to Perplexity.ai...")
    await page.get("https://www.perplexity.ai/")
    await asyncio.sleep(3)

    # Perform search
    print("\n5. Performing test search...")
    search_input = None
    for selector in SELECTORS['search_input']:
        try:
            search_input = await page.find(selector, timeout=2)
            if search_input:
                print(f"   Found search input with selector: {selector}")
                break
        except:
            continue

    if not search_input:
        print("   ERROR: Could not find search input!")
        return

    await search_input.click()
    print(f"   Typing query: {query}")
    await search_input.send_keys(query)
    await asyncio.sleep(0.5)

    # Submit with triple fallback (from working code)
    print("   Submitting search...")

    # Method 1: Send newline
    await search_input.send_keys('\n')
    await asyncio.sleep(0.5)

    # Method 2: Send Enter key via CDP
    try:
        await page.send(cdp.input_.dispatch_key_event(
            type_='keyDown',
            key='Enter',
            code='Enter',
            windows_virtual_key_code=13,
            native_virtual_key_code=13
        ))
        await page.send(cdp.input_.dispatch_key_event(
            type_='keyUp',
            key='Enter',
            code='Enter',
            windows_virtual_key_code=13,
            native_virtual_key_code=13
        ))
        print("   Sent Enter key via CDP")
    except Exception as e:
        print(f"   Warning: CDP Enter failed: {e}")

    await asyncio.sleep(1)

    # Method 3: Click search button
    try:
        search_button = await page.select(SELECTORS['search_button'][0], timeout=2)
        if search_button:
            await search_button.click()
            print("   Clicked search button")
    except:
        pass

    print("   ✓ Search submitted")

    # Wait for navigation to results page
    print("\n6. Waiting for results page to load...")
    await asyncio.sleep(3)

    # Check if we're on a search results page
    current_url = page.url
    print(f"   Current URL: {current_url}")

    if 'search' not in current_url.lower():
        print("   ⚠ Warning: URL doesn't contain 'search' - may not be on results page")

    # Wait for answer to appear
    print("\n7. Waiting for answer to generate...")
    answer_appeared = False
    for i in range(30):
        try:
            # Look for answer content (main article or answer container)
            main = await page.select('main')
            if main and len(main.text_all) > 100:
                print(f"   ✓ Answer content detected (length: {len(main.text_all)})")
                answer_appeared = True
                break
        except:
            pass
        await asyncio.sleep(1)
        if i % 5 == 0:
            print(f"   ... still waiting ({i}s)")

    if not answer_appeared:
        print("   ⚠ Warning: Answer may not have loaded")

    # Wait for content stability
    print("\n8. Waiting for answer generation to complete...")
    await wait_for_content_stability(page, max_wait=20)

    # Scroll down to see the full results and sources button at bottom
    print("\n9. Scrolling down to see full results and sources button...")
    try:
        # Scroll to bottom of page to reveal sources button
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        print("   ✓ Scrolled to bottom of page")

        # Get page height to confirm we scrolled
        scroll_info = await page.evaluate("({ scrollTop: window.scrollY, height: document.body.scrollHeight })")
        print(f"   Scroll position: {scroll_info}")
    except Exception as e:
        print(f"   ⚠ Could not scroll: {e}")

    print_section("STRATEGY 1: TEXT-BASED SEARCH")
    print("Attempting: page.find('sources', best_match=True)")

    try:
        button = await page.find("sources", best_match=True, timeout=5)
        if button:
            text = button.text_all.strip() if button.text_all else "N/A"
            tag = button.tag_name
            print(f"✓ Found element!")
            print(f"  Tag: {tag}")
            print(f"  Text: '{text}'")
            print(f"  Visible: {await button.get_attribute('style')}")

            # Get attributes
            for attr in ['class', 'id', 'data-testid', 'aria-label', 'role']:
                value = await button.get_attribute(attr)
                if value:
                    print(f"  {attr}: {value}")
        else:
            print("✗ No element found with text 'sources'")
    except Exception as e:
        print(f"✗ Error: {e}")

    print_section("STRATEGY 2: BUTTON WITH TEXT CONTAINING 'SOURCE'")
    print("Searching all buttons for text containing 'source'...")

    try:
        result = await page.evaluate("""
            Array.from(document.querySelectorAll('button')).map(btn => ({
                text: btn.textContent.trim(),
                class: btn.className,
                id: btn.id,
                'data-testid': btn.getAttribute('data-testid'),
                'aria-label': btn.getAttribute('aria-label'),
                visible: btn.offsetParent !== null
            })).filter(btn => btn.text.toLowerCase().includes('source'))
        """)

        if result and len(result) > 0:
            print(f"✓ Found {len(result)} button(s) with 'source' in text:")
            for idx, btn_data in enumerate(result, 1):
                print(f"\n  Button {idx}:")
                for key, value in btn_data.items():
                    if value:
                        print(f"    {key}: {value}")
        else:
            print("✗ No buttons found with 'source' in text")
    except Exception as e:
        print(f"✗ Error: {e}")

    print_section("STRATEGY 3: CSS SELECTORS")

    selectors_to_test = [
        ('button:has-text("sources")', 'Button with text "sources"'),
        ('[aria-label*="source" i]', 'aria-label containing "source"'),
        ('[aria-label*="citation" i]', 'aria-label containing "citation"'),
        ('button[class*="source"]', 'Button class containing "source"'),
        ('button[class*="citation"]', 'Button class containing "citation"'),
        ('footer button', 'Button in footer'),
        ('[data-testid*="source"] button', 'Button with data-testid containing "source"'),
        ('[role="button"]:has-text("source")', 'Role button with text "source"'),
    ]

    for selector, description in selectors_to_test:
        try:
            elements = await page.query_selector_all(selector)
            if elements and len(elements) > 0:
                print(f"\n✓ {description}")
                print(f"  Selector: {selector}")
                print(f"  Found: {len(elements)} element(s)")

                # Show first element details
                elem = elements[0]
                text = elem.text_all.strip() if elem.text_all else "N/A"
                print(f"  First element text: '{text}'")
            else:
                print(f"\n✗ {description}")
                print(f"  Selector: {selector}")
        except Exception as e:
            print(f"\n✗ {description}")
            print(f"  Selector: {selector}")
            print(f"  Error: {e}")

    print_section("STRATEGY 4: JAVASCRIPT DOM EXPLORATION")
    print("Finding ALL elements with text containing 'source'...")

    try:
        result = await page.evaluate("""
            Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent.trim().toLowerCase();
                return text.includes('source') && el.children.length === 0;
            }).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 100),
                class: el.className,
                id: el.id,
                'data-testid': el.getAttribute('data-testid'),
                'aria-label': el.getAttribute('aria-label'),
                clickable: el.tagName === 'BUTTON' || el.tagName === 'A' || el.onclick !== null
            })).slice(0, 20)
        """)

        if result and len(result) > 0:
            print(f"✓ Found {len(result)} elements (showing first 20):")
            for idx, el_data in enumerate(result, 1):
                print(f"\n  Element {idx}:")
                for key, value in el_data.items():
                    if value:
                        display_value = str(value)[:100]
                        print(f"    {key}: {display_value}")
        else:
            print("✗ No elements found with 'source' in text")
    except Exception as e:
        print(f"✗ Error: {e}")

    print_section("STRATEGY 5: FOOTER EXPLORATION")
    print("Looking specifically in footer/bottom area...")

    try:
        result = await page.evaluate("""
            const footer = document.querySelector('footer') || document.querySelector('main');
            if (!footer) {
                return null;
            }

            // Get all clickable elements in footer area
            const clickables = Array.from(footer.querySelectorAll('button, a, [role="button"]'));

            return clickables.map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 100),
                class: el.className,
                'data-testid': el.getAttribute('data-testid'),
                'aria-label': el.getAttribute('aria-label'),
                visible: el.offsetParent !== null,
                position: el.getBoundingClientRect().top
            })).sort((a, b) => b.position - a.position).slice(0, 10);
        """)

        if result and len(result) > 0:
            print(f"✓ Found {len(result)} clickable elements in footer (top 10 by position):")
            for idx, el_data in enumerate(result, 1):
                print(f"\n  Element {idx}:")
                for key, value in el_data.items():
                    if value:
                        print(f"    {key}: {value}")
        else:
            print("✗ No clickable elements found in footer")
    except Exception as e:
        print(f"✗ Error: {e}")

    print_section("TEST: ATTEMPTING TO CLICK SOURCES BUTTON")
    print("Will try text-based search and click if found...")

    try:
        # Try text-based first
        button = await page.find("sources", best_match=True, timeout=3)

        if not button:
            # Try finding by JavaScript
            print("Text-based search failed, trying JavaScript...")
            button_data = await page.evaluate("""
                const btn = Array.from(document.querySelectorAll('button, [role="button"]'))
                    .find(el => el.textContent.toLowerCase().includes('source'));

                if (btn) {
                    return {
                        selector: btn.id ? '#' + btn.id : btn.className ? '.' + btn.className.split(' ')[0] : null,
                        text: btn.textContent.trim()
                    };
                }
                return null;
            """)

            if button_data and button_data.get('selector'):
                print(f"  Found via JavaScript: {button_data['text']}")
                button = await page.select(button_data['selector'])

        if button:
            print(f"✓ Found button to click!")
            print(f"  Text: '{button.text_all.strip()}'")

            # Count sources before clicking (multiple selectors)
            sources_before_1 = await page.query_selector_all('[data-testid*="source"] a')
            sources_before_2 = await page.query_selector_all('a[href^="http"]')
            print(f"  Sources before click:")
            print(f"    [data-testid*='source'] a: {len(sources_before_1)}")
            print(f"    a[href^='http']: {len(sources_before_2)}")

            # Click
            print("  Clicking button...")
            await button.click()
            print("  Waiting 5 seconds for expansion...")
            await asyncio.sleep(5)

            # Count sources after clicking (multiple selectors)
            sources_after_1 = await page.query_selector_all('[data-testid*="source"] a')
            sources_after_2 = await page.query_selector_all('a[href^="http"]')
            sources_after_3 = await page.query_selector_all('article a[href^="http"]')
            sources_after_4 = await page.query_selector_all('[class*="citation"] a')
            sources_after_5 = await page.query_selector_all('[class*="source"] a')

            print(f"  Sources after click:")
            print(f"    [data-testid*='source'] a: {len(sources_after_1)}")
            print(f"    a[href^='http']: {len(sources_after_2)}")
            print(f"    article a[href^='http']: {len(sources_after_3)}")
            print(f"    [class*='citation'] a: {len(sources_after_4)}")
            print(f"    [class*='source'] a: {len(sources_after_5)}")

            # Check for any changes
            if len(sources_after_2) > len(sources_before_2):
                print(f"\n✓ SUCCESS! Links increased ({len(sources_before_2)} → {len(sources_after_2)})")

                # Show details of new links
                print("\n  Sample links (first 10):")
                for idx, source in enumerate(sources_after_2[:10], 1):
                    try:
                        href = await source.get_attribute('href')
                        text = source.text_all.strip() if source.text_all else "N/A"
                        if href and href.startswith('http'):
                            print(f"    {idx}. {text[:50]}... → {href[:60]}...")
                    except:
                        pass

                # Try to identify which selector works best for expanded sources
                print("\n  Identifying best selector for expanded sources:")
                if len(sources_after_1) > 0:
                    print(f"    ✓ [data-testid*='source'] a - {len(sources_after_1)} elements")
                if len(sources_after_4) > 0:
                    print(f"    ✓ [class*='citation'] a - {len(sources_after_4)} elements")
                if len(sources_after_5) > 0:
                    print(f"    ✓ [class*='source'] a - {len(sources_after_5)} elements")
            else:
                print("\n⚠ No significant link count change detected")
                print("  Sources might be in a modal, popup, or different container")
        else:
            print("✗ Could not find sources button with any method")
    except Exception as e:
        print(f"✗ Error during click test: {e}")
        import traceback
        traceback.print_exc()

    print_section("INVESTIGATION COMPLETE")
    print("\nBrowser will remain open for manual DevTools inspection.")
    print("Recommended next steps:")
    print("  1. Press F12 to open DevTools")
    print("  2. Look for the 'x sources' button")
    print("  3. Inspect its HTML structure and attributes")
    print("  4. Note what happens when you click it manually")
    print("\nPress Ctrl+C to exit...")

    try:
        await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nExiting...")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Investigate collapsible sources button on Perplexity.ai',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--query', '-q',
        default="What are the benefits of meditation?",
        help='Search query to use (default: "What are the benefits of meditation?")'
    )

    args = parser.parse_args()

    try:
        uc.loop().run_until_complete(investigate_sources_button(args.query))
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
