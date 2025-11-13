#!/usr/bin/env python3
"""
Investigation script to monitor WHEN sources appear during Perplexity search.

This script:
1. Opens Perplexity.ai with authentication
2. Performs a search
3. Monitors the page at regular intervals to see when sources appear
4. Tests multiple selectors at each interval
5. Reports timing and availability of source elements

Usage:
    python scripts/investigate_source_timing.py
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG, SELECTORS


async def check_sources_available(page, selectors):
    """Check if sources are available using multiple selectors."""
    results = {}

    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            results[selector] = {
                'count': len(elements),
                'found': len(elements) > 0
            }

            # If found, get sample data
            if elements:
                samples = []
                for elem in elements[:2]:  # First 2 examples
                    try:
                        if elem.tag_name == 'a':
                            href = await elem.get_attribute('href')
                            text = elem.text_all.strip() if elem.text_all else ""
                            samples.append({'href': href, 'text': text[:50]})
                        else:
                            # For non-link elements, get nested links
                            links = await elem.query_selector_all('a')
                            if links:
                                href = await links[0].get_attribute('href')
                                text = links[0].text_all.strip() if links[0].text_all else ""
                                samples.append({'href': href, 'text': text[:50]})
                    except:
                        pass

                results[selector]['samples'] = samples

        except Exception as e:
            results[selector] = {
                'count': 0,
                'found': False,
                'error': str(e)
            }

    return results


async def monitor_search_lifecycle(page, query, duration=30, interval=1):
    """Monitor page for sources at regular intervals during search."""

    selectors_to_monitor = [
        # Current codebase selector
        '[data-testid*="source"] a',

        # Common alternatives
        '[data-testid="citation"] a',
        '[class*="citation"] a',
        '[class*="source"] a',
        '[aria-label*="source"]',

        # Container-based
        '[data-testid*="answer"] a[href^="http"]',

        # Numbered references
        'sup a',

        # Bottom sources
        'footer a[href^="http"]',
    ]

    print("\n" + "="*80)
    print("MONITORING SOURCE APPEARANCE OVER TIME")
    print("="*80)
    print(f"Query: {query}")
    print(f"Duration: {duration} seconds")
    print(f"Interval: {interval} second(s)")
    print(f"Monitoring {len(selectors_to_monitor)} selectors")
    print("="*80)

    # Find and activate search input
    print("\nInitiating search...")
    search_input = None
    for selector in SELECTORS['search_input']:
        try:
            search_input = await page.find(selector, timeout=2)
            if search_input:
                print(f"Found search input with selector: {selector}")
                break
        except:
            continue

    if not search_input:
        print("ERROR: Could not find search input with any selector!")
        return

    await search_input.click()
    await search_input.send_keys(query)
    await asyncio.sleep(0.5)

    # Submit search and start timer
    print("Submitting search...")
    await search_input.send_keys('\n')
    start_time = datetime.now()

    # Monitor at intervals
    timeline = []
    for check_num in range(int(duration / interval)):
        elapsed = (datetime.now() - start_time).total_seconds()

        # Check sources
        results = await check_sources_available(page, selectors_to_monitor)

        # Record this checkpoint
        checkpoint = {
            'elapsed': elapsed,
            'check_num': check_num + 1,
            'results': results
        }
        timeline.append(checkpoint)

        # Print summary
        found_any = any(r['found'] for r in results.values())
        status = "✓ SOURCES FOUND" if found_any else "✗ No sources yet"

        print(f"\n[{elapsed:5.1f}s] Check #{check_num + 1}: {status}")

        for selector, data in results.items():
            if data['found']:
                samples_str = ""
                if 'samples' in data:
                    samples_str = f" | Examples: {len(data['samples'])}"
                print(f"  ✓ {selector}: {data['count']} elements{samples_str}")

        # Wait for next interval
        await asyncio.sleep(interval)

    return timeline


async def analyze_timeline(timeline):
    """Analyze timeline to determine when sources first appeared."""
    print("\n" + "="*80)
    print("TIMELINE ANALYSIS")
    print("="*80)

    # For each selector, find when it first appeared
    selector_first_appearance = {}

    for checkpoint in timeline:
        for selector, data in checkpoint['results'].items():
            if data['found'] and selector not in selector_first_appearance:
                selector_first_appearance[selector] = {
                    'elapsed': checkpoint['elapsed'],
                    'count': data['count'],
                    'samples': data.get('samples', [])
                }

    if not selector_first_appearance:
        print("\n⚠ NO SOURCES FOUND during entire monitoring period!")
        print("\nPossible reasons:")
        print("  1. Sources appear after the monitoring period ended")
        print("  2. Sources use different selectors than tested")
        print("  3. Sources are dynamically loaded via JavaScript")
        print("  4. Sources are in shadow DOM or iframes")
        return

    print(f"\n✓ Found sources with {len(selector_first_appearance)} different selectors")
    print("\nFirst appearance times (earliest first):")

    # Sort by appearance time
    sorted_selectors = sorted(
        selector_first_appearance.items(),
        key=lambda x: x[1]['elapsed']
    )

    for selector, info in sorted_selectors:
        print(f"\n  [{info['elapsed']:5.1f}s] {selector}")
        print(f"            Count: {info['count']}")
        if info['samples']:
            print(f"            Samples:")
            for sample in info['samples']:
                print(f"              - {sample['text']}")
                print(f"                {sample['href'][:70]}...")

    # Recommendation
    fastest = sorted_selectors[0]
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print(f"\nFastest selector (appeared at {fastest[1]['elapsed']:.1f}s):")
    print(f"  {fastest[0]}")
    print(f"\nThis selector found {fastest[1]['count']} source elements")


async def main():
    print("="*80)
    print("PERPLEXITY SOURCE TIMING INVESTIGATION")
    print("="*80)

    # Load cookies
    print("\n1. Loading authentication cookies...")
    cookies = load_cookies()
    print(f"   Loaded {len(cookies)} cookies")

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

    # Monitor search
    test_query = "What are the health benefits of green tea?"
    timeline = await monitor_search_lifecycle(
        page,
        test_query,
        duration=30,  # Monitor for 30 seconds
        interval=1    # Check every 1 second
    )

    # Analyze results
    await analyze_timeline(timeline)

    # Keep browser open for manual inspection
    print("\n" + "="*80)
    print("Browser will remain open for manual inspection.")
    print("Press Ctrl+C to exit...")
    print("="*80)

    try:
        await asyncio.sleep(3600)
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
