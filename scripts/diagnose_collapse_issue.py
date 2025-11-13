#!/usr/bin/env python3
"""
Diagnostic script to investigate sources panel collapse failure.

This script:
1. Opens Perplexity.ai with authentication
2. Performs a search automatically
3. Waits for results to load
4. Inspects the sources button in BOTH collapsed and expanded states
5. Tests clicking to collapse and logs all relevant information
6. Provides actionable recommendations for fixing selectors

Usage:
    python scripts/diagnose_collapse_issue.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG, TIMEOUTS, SELECTORS


async def count_source_links(page):
    """Count all source links on the page."""
    try:
        links = await page.query_selector_all('a[href^="http"]')
        return len(links)
    except Exception as e:
        print(f"Error counting links: {e}")
        return 0


async def inspect_sources_button(page, state_name):
    """Inspect sources button and log all relevant information."""
    print(f"\n{'='*80}")
    print(f"INSPECTING SOURCES BUTTON - {state_name.upper()} STATE")
    print(f"{'='*80}")

    # Strategy 1: Text-based search
    print("\n1. Testing text-based search: page.find('sources')...")
    try:
        button = await page.find("sources", best_match=True, timeout=2)
        if button:
            print("   ✓ Found via text search")
            text = button.text_all.strip() if button.text_all else ""
            print(f"   Text content: '{text}'")

            # Get attributes
            tag_name = button.tag_name
            classes = await button.get_attribute("class")
            aria_label = await button.get_attribute("aria-label")
            data_testid = await button.get_attribute("data-testid")
            role = await button.get_attribute("role")

            print(f"   Tag: {tag_name}")
            print(f"   Classes: {classes}")
            if aria_label:
                print(f"   Aria-label: {aria_label}")
            if data_testid:
                print(f"   Data-testid: {data_testid}")
            if role:
                print(f"   Role: {role}")
        else:
            print("   ✗ Not found via text search")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Strategy 2: Try configured CSS selectors
    print("\n2. Testing configured CSS selectors...")
    configured_selectors = [
        'button:has-text("source")',
        '[class*="cursor-pointer"][class*="rounded-full"]',
    ]

    for selector in configured_selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"\n   ✓ Selector: {selector}")
                print(f"     Found: {len(elements)} elements")

                # Inspect each element
                for idx, elem in enumerate(elements[:3], 1):
                    text = elem.text_all.strip() if elem.text_all else ""
                    classes = await elem.get_attribute("class")
                    print(f"     Element {idx}:")
                    print(f"       Text: '{text}'")
                    print(f"       Classes: {classes}")
            else:
                print(f"   ✗ Selector: {selector} - No matches")
        except Exception as e:
            print(f"   ✗ Selector: {selector} - Error: {e}")

    # Strategy 3: Try SmartClicker candidates
    print("\n3. Testing SmartClicker selector candidates...")
    smartclicker_selectors = [
        '[class*="cursor-pointer"][class*="rounded-full"]',
        'button:has-text("source")',
        'button[class*="source"]',
    ]

    for selector in smartclicker_selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"\n   ✓ Selector: {selector}")
                print(f"     Found: {len(elements)} elements")

                # Filter for elements containing "source" text
                for idx, elem in enumerate(elements, 1):
                    text = elem.text_all.strip().lower() if elem.text_all else ""
                    if 'source' in text:
                        print(f"     Match {idx} (contains 'source'):")
                        print(f"       Text: '{elem.text_all.strip()}'")
                        classes = await elem.get_attribute("class")
                        print(f"       Classes: {classes}")
            else:
                print(f"   ✗ Selector: {selector} - No matches")
        except Exception as e:
            print(f"   ✗ Selector: {selector} - Error: {e}")

    # Strategy 4: JavaScript exploration for buttons containing "source"
    print("\n4. JavaScript exploration - all buttons with 'source' text...")
    js_code = """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
        const matches = buttons.filter(b =>
            b.textContent.toLowerCase().includes('source')
        ).map(b => ({
            tag: b.tagName,
            text: b.textContent.trim(),
            classes: b.className,
            ariaLabel: b.getAttribute('aria-label'),
            dataTestid: b.getAttribute('data-testid'),
            role: b.getAttribute('role'),
            visible: b.offsetParent !== null
        }));
        return matches;
    })();
    """

    try:
        results = await page.evaluate(js_code)
        if results:
            print(f"   Found {len(results)} buttons with 'source' text:")
            for idx, result in enumerate(results, 1):
                print(f"\n   Button {idx}:")
                print(f"     Tag: {result['tag']}")
                print(f"     Text: '{result['text']}'")
                print(f"     Classes: {result['classes']}")
                print(f"     Aria-label: {result['ariaLabel']}")
                print(f"     Data-testid: {result['dataTestid']}")
                print(f"     Role: {result['role']}")
                print(f"     Visible: {result['visible']}")
        else:
            print("   ✗ No buttons with 'source' text found")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Strategy 5: Look for elements with collapse/expand indicators
    print("\n5. Looking for collapse/expand indicators...")
    js_code = """
    (() => {
        const keywords = ['collapse', 'expand', 'hide', 'show', 'toggle'];
        const elements = Array.from(document.querySelectorAll('*'));
        const matches = elements.filter(el => {
            const text = el.textContent.toLowerCase();
            const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
            const ariaExpanded = el.getAttribute('aria-expanded');

            return (keywords.some(kw => text.includes(kw) || ariaLabel.includes(kw)) ||
                    ariaExpanded !== null) &&
                   text.includes('source');
        }).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().substring(0, 100),
            ariaLabel: el.getAttribute('aria-label'),
            ariaExpanded: el.getAttribute('aria-expanded'),
            classes: el.className
        }));
        return matches.slice(0, 10);  // Limit to first 10
    })();
    """

    try:
        results = await page.evaluate(js_code)
        if results:
            print(f"   Found {len(results)} elements with collapse/expand indicators:")
            for idx, result in enumerate(results, 1):
                print(f"\n   Element {idx}:")
                print(f"     Tag: {result['tag']}")
                print(f"     Text: '{result['text']}'")
                print(f"     Aria-label: {result['ariaLabel']}")
                print(f"     Aria-expanded: {result['ariaExpanded']}")
                print(f"     Classes: {result['classes']}")
        else:
            print("   ✗ No elements with collapse/expand indicators found")
    except Exception as e:
        print(f"   ✗ Error: {e}")


async def test_collapse_click(page):
    """Attempt to click the sources button to collapse."""
    print(f"\n{'='*80}")
    print("TESTING COLLAPSE CLICK")
    print(f"{'='*80}")

    # Count links before
    links_before = await count_source_links(page)
    print(f"\nLinks before collapse: {links_before}")

    # Try to find and click the button
    print("\nAttempting to find and click sources button...")

    # Try text-based search first
    try:
        button = await page.find("sources", best_match=True, timeout=2)
        if button:
            print("✓ Found button via text search")
            text = button.text_all.strip() if button.text_all else ""
            print(f"  Button text: '{text}'")

            print("\n  Clicking button...")
            await button.click()
            await asyncio.sleep(2)  # Wait for collapse animation

            # Count links after
            links_after = await count_source_links(page)
            print(f"\nLinks after collapse: {links_after}")
            print(f"Difference: {links_before - links_after}")

            if links_after < links_before:
                print("✓ Collapse succeeded (link count decreased)")
            elif links_after > links_before:
                print("⚠ Collapse may have expanded instead (link count increased)")
            else:
                print("✗ No change in link count")

            return True
        else:
            print("✗ Button not found via text search")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def generate_recommendations(page):
    """Generate actionable recommendations based on findings."""
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")

    print("\nBased on the diagnostic results above:")
    print("\n1. Check which selectors successfully found the button in BOTH states")
    print("2. Look for selectors that work in both collapsed and expanded states")
    print("3. Note any aria-expanded attributes that could help detect state")
    print("4. Consider using JavaScript-based element finding for reliability")
    print("\n5. Update src/config.py SELECTORS['sources']['collapse_button'] with:")
    print("   - Selectors that matched in BOTH collapsed and expanded states")
    print("   - Prioritize data-testid or role-based selectors for stability")
    print("   - Keep text-based search as fallback if it works in both states")
    print("\n6. Consider using aria-expanded to detect state instead of text matching")
    print("\n7. Test the updated selectors with this script before deploying")


async def main():
    print("="*80)
    print("SOURCES PANEL COLLAPSE DIAGNOSTIC TOOL")
    print("="*80)

    # Load cookies
    print("\n1. Loading authentication cookies...")
    cookies = load_cookies()
    print(f"   Loaded {len(cookies)} cookies")

    # Start browser
    print("\n2. Starting browser...")
    browser = await uc.start(
        browser_args=BROWSER_CONFIG['args'],
        headless=False  # Must be visible for Perplexity
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

    # Perform a search
    print("\n5. Performing test search...")
    test_query = "What is Python programming?"

    # Find search input
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
        print("   Keeping browser open for manual inspection...")
        print("   Press Ctrl+C to exit...")
        try:
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            pass
        return

    # Type and submit query
    print(f"   Typing query: {test_query}")
    await search_input.click()
    print("   Clicked input, typing...")

    # Type character by character for better visibility
    for char in test_query:
        await search_input.send_keys(char)
        await asyncio.sleep(0.05)

    print("   Typed query, submitting...")
    await asyncio.sleep(0.5)

    # Store initial URL to verify search started
    initial_url = page.url
    print(f"   Current URL: {initial_url}")

    await search_input.send_keys('\n')
    print("   ✓ Sent Enter key")

    # Wait for URL change to confirm search started
    await asyncio.sleep(2)
    new_url = page.url
    print(f"   New URL: {new_url}")

    if new_url != initial_url:
        print("   ✓ Search initiated (URL changed)")
    else:
        print("   ⚠ URL unchanged - search may not have started")
        print("   Trying alternative submission with CDP Enter key...")
        # Try CDP key event as fallback
        await page.send(uc.cdp.input_.dispatch_key_event(
            type_='keyDown', key='Enter', code='Enter',
            windows_virtual_key_code=13, native_virtual_key_code=13
        ))
        await page.send(uc.cdp.input_.dispatch_key_event(
            type_='keyUp', key='Enter', code='Enter',
            windows_virtual_key_code=13, native_virtual_key_code=13
        ))
        await asyncio.sleep(2)
        print(f"   URL after CDP Enter: {page.url}")

    # Wait for results with progress indicators
    print("\n6. Waiting for results to generate...")
    for i in range(15):  # Increased to 15 seconds
        await asyncio.sleep(1)
        print(f"   Waiting... {i+1}/15 seconds")

    # PHASE 1: Inspect in initial state (likely collapsed or auto-expanded)
    await inspect_sources_button(page, "INITIAL")

    # Wait a bit
    await asyncio.sleep(2)

    # PHASE 2: Click to toggle state
    print(f"\n7. Toggling sources state...")
    clicked = await test_collapse_click(page)

    if clicked:
        await asyncio.sleep(2)

        # PHASE 3: Inspect in toggled state
        await inspect_sources_button(page, "TOGGLED")

    # Generate recommendations
    await generate_recommendations(page)

    # Keep browser open for manual inspection
    print(f"\n{'='*80}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*80}")
    print("\nBrowser will remain open for manual DevTools inspection.")
    print("Press F12 to open DevTools and verify the findings above.")
    print("\nPress Ctrl+C to exit...")

    try:
        await asyncio.sleep(3600)  # Keep open for 1 hour
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    try:
        uc.loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
