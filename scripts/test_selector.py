#!/usr/bin/env python3
"""
Quick selector testing script.

Allows you to quickly test if a specific CSS selector finds source elements.

Usage:
    python scripts/test_selector.py '[data-testid*="source"] a'
    python scripts/test_selector.py 'footer a[href^="http"]'
    python scripts/test_selector.py --query "What is AI?" '.citation a'
"""

import asyncio
import sys
import os
from pathlib import Path
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG, SELECTORS


async def test_selector(selector, query="What is Python programming?"):
    """Test a specific selector after performing a search."""

    print("="*80)
    print("QUICK SELECTOR TEST")
    print("="*80)
    print(f"Query: {query}")
    print(f"Selector: {selector}")
    print("="*80)

    # Load cookies
    print("\n1. Loading cookies...")
    cookies = load_cookies()

    # Start browser
    print("2. Starting browser...")
    browser = await uc.start(
        browser_args=BROWSER_CONFIG['args'],
        headless=False
    )

    page = await browser.get("about:blank")

    # Set cookies
    print("3. Setting cookies...")
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
        except:
            pass

    # Navigate
    print("4. Navigating to Perplexity...")
    await page.get("https://www.perplexity.ai/")
    await asyncio.sleep(3)

    # Search
    print("5. Performing search...")
    search_input = None
    for sel in SELECTORS['search_input']:
        try:
            search_input = await page.find(sel, timeout=2)
            if search_input:
                print(f"   Found search input with selector: {sel}")
                break
        except:
            continue

    if not search_input:
        print("   ERROR: Could not find search input with any selector!")
        return

    await search_input.click()
    await search_input.send_keys(query)
    await asyncio.sleep(0.5)
    await search_input.send_keys('\n')

    # Wait for results
    print("6. Waiting for results (15 seconds)...")
    await asyncio.sleep(15)

    # Test selector
    print(f"\n7. Testing selector: {selector}")
    try:
        elements = await page.query_selector_all(selector)

        print(f"\n{'='*80}")
        print("RESULTS")
        print("="*80)

        if not elements:
            print("\n✗ SELECTOR FOUND 0 ELEMENTS")
            print("\nPossible reasons:")
            print("  - Selector is incorrect")
            print("  - Sources haven't loaded yet")
            print("  - Sources use different structure")
            print("\nTry:")
            print("  - Wait longer")
            print("  - Use investigate_sources.py to explore all selectors")
            print("  - Manually inspect with DevTools (F12)")
        else:
            print(f"\n✓ SELECTOR FOUND {len(elements)} ELEMENTS")

            # Show details for each element
            for idx, elem in enumerate(elements[:10], 1):  # First 10
                print(f"\n--- Element {idx} ---")

                # Get tag name
                tag = elem.tag_name
                print(f"  Tag: {tag}")

                # Get text
                text = elem.text_all.strip() if elem.text_all else ""
                if text:
                    display_text = text[:100] + "..." if len(text) > 100 else text
                    print(f"  Text: {display_text}")

                # Get href if it's a link
                if tag == 'a':
                    href = await elem.get_attribute('href')
                    if href:
                        display_href = href[:70] + "..." if len(href) > 70 else href
                        print(f"  Href: {display_href}")

                # Get important attributes
                for attr in ['data-testid', 'class', 'aria-label', 'id']:
                    value = await elem.get_attribute(attr)
                    if value:
                        print(f"  {attr}: {value}")

                # If not a link, check for nested links
                if tag != 'a':
                    nested_links = await elem.query_selector_all('a')
                    if nested_links:
                        print(f"  Contains {len(nested_links)} nested links")
                        first_link = nested_links[0]
                        nested_href = await first_link.get_attribute('href')
                        nested_text = first_link.text_all.strip() if first_link.text_all else ""
                        if nested_href:
                            print(f"    First link: {nested_href[:60]}...")
                        if nested_text:
                            print(f"    Link text: {nested_text[:50]}...")

            if len(elements) > 10:
                print(f"\n... and {len(elements) - 10} more elements")

            # Summary
            print(f"\n{'='*80}")
            print("SUMMARY")
            print("="*80)
            print(f"\n✓ Selector works!")
            print(f"  Found: {len(elements)} elements")
            print(f"  Selector: {selector}")

            # Check if they're actually links
            link_count = sum(1 for elem in elements if elem.tag_name == 'a')
            if link_count > 0:
                print(f"  Direct links: {link_count}")
            else:
                print(f"  Note: Elements are not <a> tags, may need nested selector")

    except Exception as e:
        print(f"\n✗ ERROR TESTING SELECTOR")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

    # Keep open
    print(f"\n{'='*80}")
    print("Browser will remain open for manual inspection.")
    print("Press Ctrl+C to exit...")
    print("="*80)

    try:
        await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nExiting...")


def main():
    parser = argparse.ArgumentParser(
        description='Test a CSS selector for extracting Perplexity sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_selector.py '[data-testid*="source"] a'
  python scripts/test_selector.py --query "What is AI?" 'footer a'
  python scripts/test_selector.py '.citation-link'
        """
    )

    parser.add_argument(
        'selector',
        help='CSS selector to test (quote if contains special chars)'
    )

    parser.add_argument(
        '--query', '-q',
        default="What is Python programming?",
        help='Search query to use (default: "What is Python programming?")'
    )

    args = parser.parse_args()

    try:
        uc.loop().run_until_complete(test_selector(args.selector, args.query))
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
