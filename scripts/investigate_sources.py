#!/usr/bin/env python3
"""
Investigation script to inspect Perplexity.ai source elements.

This script:
1. Opens Perplexity.ai with authentication
2. Performs a search automatically
3. Waits for results to load
4. Extracts and prints ALL possible source-related elements with their attributes
5. Keeps browser open for manual DevTools inspection

Usage:
    python scripts/investigate_sources.py
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


async def inspect_all_links(page):
    """Extract and display all links with their attributes."""
    print("\n" + "="*80)
    print("INSPECTING ALL LINKS ON PAGE")
    print("="*80)

    # Get all links
    all_links = await page.query_selector_all("a")

    print(f"\nTotal links found: {len(all_links)}")

    for idx, link in enumerate(all_links, 1):
        try:
            # Get all attributes
            href = await link.get_attribute("href")
            text = link.text_all.strip() if link.text_all else ""
            data_testid = await link.get_attribute("data-testid")
            classes = await link.get_attribute("class")
            aria_label = await link.get_attribute("aria-label")
            target = await link.get_attribute("target")

            # Only print if it might be a source (has href and some identifying info)
            if href:
                print(f"\n--- Link {idx} ---")
                print(f"  href: {href}")
                print(f"  text: {text[:100]}..." if len(text) > 100 else f"  text: {text}")
                if data_testid:
                    print(f"  data-testid: {data_testid}")
                if classes:
                    print(f"  class: {classes}")
                if aria_label:
                    print(f"  aria-label: {aria_label}")
                if target:
                    print(f"  target: {target}")

        except Exception as e:
            print(f"  Error inspecting link {idx}: {e}")


async def inspect_source_selectors(page):
    """Try various selectors that might contain sources."""
    print("\n" + "="*80)
    print("TESTING VARIOUS SOURCE SELECTORS")
    print("="*80)

    selectors_to_test = [
        # Current selector from codebase
        '[data-testid*="source"] a',
        '[data-testid*="source"]',

        # Common patterns for sources
        '[data-testid="citation"]',
        '[data-testid="citation"] a',
        '.citation a',
        '.source a',
        '[class*="citation"]',
        '[class*="source"]',
        '[class*="reference"]',
        '[aria-label*="source"]',
        '[aria-label*="citation"]',

        # Container approaches
        '[data-testid*="answer"] a[href^="http"]',
        'main a[href^="http"]',

        # Numbered citations
        'sup a',
        '[role="doc-noteref"]',

        # Footer/bottom sources
        'footer a',
        '[class*="sources"] a',
        '[class*="references"] a',
    ]

    for selector in selectors_to_test:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"\n✓ Selector: {selector}")
                print(f"  Found: {len(elements)} elements")

                # Show first few examples
                for idx, elem in enumerate(elements[:3], 1):
                    href = await elem.get_attribute("href") if elem.tag_name == "a" else "N/A"
                    text = elem.text_all.strip() if elem.text_all else ""
                    print(f"    Example {idx}: href={href[:60]}... text={text[:50]}...")
            else:
                print(f"\n✗ Selector: {selector}")
                print(f"  Found: 0 elements")

        except Exception as e:
            print(f"\n⚠ Selector: {selector}")
            print(f"  Error: {e}")


async def inspect_dom_structure(page):
    """Use JavaScript to explore DOM structure for sources."""
    print("\n" + "="*80)
    print("JAVASCRIPT DOM EXPLORATION")
    print("="*80)

    # Find all elements with "source", "citation", or "reference" in attributes
    js_code = """
    (() => {
        const results = [];
        const keywords = ['source', 'citation', 'reference', 'cite'];

        // Check all elements
        const allElements = document.querySelectorAll('*');

        allElements.forEach((el, idx) => {
            const attrs = {};
            let hasKeyword = false;

            // Check all attributes
            for (let attr of el.attributes) {
                const attrName = attr.name.toLowerCase();
                const attrValue = attr.value.toLowerCase();

                if (keywords.some(kw => attrName.includes(kw) || attrValue.includes(kw))) {
                    hasKeyword = true;
                    attrs[attr.name] = attr.value;
                }
            }

            if (hasKeyword) {
                results.push({
                    tag: el.tagName,
                    attributes: attrs,
                    text: el.textContent.substring(0, 100),
                    html: el.outerHTML.substring(0, 200)
                });
            }
        });

        return results;
    })();
    """

    try:
        results = await page.evaluate(js_code)
        print(f"\nFound {len(results)} elements with source/citation/reference keywords")

        for idx, result in enumerate(results[:10], 1):  # Limit to first 10
            print(f"\n--- Element {idx} ---")
            print(f"  Tag: {result['tag']}")
            print(f"  Attributes: {result['attributes']}")
            print(f"  Text: {result['text']}")
            print(f"  HTML: {result['html']}")

    except Exception as e:
        print(f"Error executing JavaScript: {e}")


async def main():
    print("="*80)
    print("PERPLEXITY SOURCE EXTRACTION INVESTIGATION")
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

    # Find search input using selectors from working config
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
        print("   ERROR: Could not find search input with any selector!")
        print("   Keeping browser open for manual inspection...")
        print("   Press Ctrl+C to exit...")
        try:
            await asyncio.sleep(3600)  # Keep open for 1 hour
        except KeyboardInterrupt:
            pass
        return

    # Type query
    print(f"   Typing query: {test_query}")
    await search_input.click()
    await search_input.send_keys(test_query)
    await asyncio.sleep(1)

    # Submit
    await search_input.send_keys('\n')
    print("   Submitted search")

    # Wait for results
    print("\n6. Waiting for results...")
    await asyncio.sleep(10)  # Give time for answer to generate

    # Run all inspections
    await inspect_source_selectors(page)
    await inspect_all_links(page)
    await inspect_dom_structure(page)

    # Keep browser open
    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    print("\nBrowser will remain open for manual DevTools inspection.")
    print("Recommended next steps:")
    print("  1. Press F12 to open DevTools")
    print("  2. Inspect elements that look like sources")
    print("  3. Note their selectors, attributes, and structure")
    print("  4. Look for patterns in how sources are rendered")
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
