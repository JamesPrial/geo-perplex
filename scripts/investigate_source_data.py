#!/usr/bin/env python3
"""
Investigation script to explore WHERE and HOW source data is stored in Perplexity.

This script uses JavaScript to explore:
1. React component props and state
2. Window object for API responses
3. Network requests/responses
4. Shadow DOM
5. Data attributes
6. Hidden elements

Usage:
    python scripts/investigate_source_data.py
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG, SELECTORS


async def explore_react_data(page):
    """Explore React component tree for source data."""
    print("\n" + "="*80)
    print("EXPLORING REACT COMPONENT DATA")
    print("="*80)

    js_code = """
    (() => {
        const results = {
            foundReact: false,
            components: [],
            props: []
        };

        // Find React root
        const root = document.querySelector('#__next') || document.querySelector('main');
        if (!root) return results;

        // Get React Fiber (internal React structure)
        const fiberKey = Object.keys(root).find(key => key.startsWith('__reactFiber'));
        if (!fiberKey) return results;

        results.foundReact = true;

        // Search for source/citation data in props
        function searchProps(obj, path = '', depth = 0) {
            if (depth > 5 || !obj || typeof obj !== 'object') return;

            for (let key in obj) {
                const lowerKey = key.toLowerCase();
                const currentPath = path ? `${path}.${key}` : key;

                if (lowerKey.includes('source') ||
                    lowerKey.includes('citation') ||
                    lowerKey.includes('reference') ||
                    lowerKey.includes('url')) {

                    results.props.push({
                        path: currentPath,
                        key: key,
                        value: JSON.stringify(obj[key]).substring(0, 200)
                    });
                }

                if (depth < 3) {
                    searchProps(obj[key], currentPath, depth + 1);
                }
            }
        }

        const fiber = root[fiberKey];
        if (fiber) {
            searchProps(fiber.memoizedProps);
            searchProps(fiber.memoizedState);
        }

        return results;
    })();
    """

    try:
        results = await page.evaluate(js_code)

        if not results['foundReact']:
            print("  ✗ No React root found")
            return

        print(f"  ✓ React root found")
        print(f"  Found {len(results['props'])} potential source-related props")

        for prop in results['props'][:10]:  # Show first 10
            print(f"\n    Path: {prop['path']}")
            print(f"    Value: {prop['value']}")

    except Exception as e:
        print(f"  Error: {e}")


async def explore_window_objects(page):
    """Explore window object for API data."""
    print("\n" + "="*80)
    print("EXPLORING WINDOW OBJECT DATA")
    print("="*80)

    js_code = """
    (() => {
        const results = {
            apiData: [],
            dataLayers: []
        };

        // Check common API response storage locations
        const checkPaths = [
            'window.__NEXT_DATA__',
            'window.__INITIAL_STATE__',
            'window.__APOLLO_STATE__',
            'window.PERPLEXITY_DATA',
            'window.initialData'
        ];

        for (let path of checkPaths) {
            try {
                const value = eval(path);
                if (value) {
                    results.apiData.push({
                        path: path,
                        hasData: true,
                        sample: JSON.stringify(value).substring(0, 500)
                    });
                }
            } catch (e) {
                // Path doesn't exist
            }
        }

        // Search all window properties for source-like data
        for (let key in window) {
            try {
                const lowerKey = key.toLowerCase();
                if (lowerKey.includes('source') ||
                    lowerKey.includes('citation') ||
                    lowerKey.includes('data') ||
                    lowerKey.includes('api')) {

                    const value = window[key];
                    if (typeof value === 'object' && value !== null) {
                        results.dataLayers.push({
                            key: key,
                            type: typeof value,
                            sample: JSON.stringify(value).substring(0, 300)
                        });
                    }
                }
            } catch (e) {
                // Skip properties that throw errors
            }
        }

        return results;
    })();
    """

    try:
        results = await page.evaluate(js_code)

        print(f"\n  API Data Stores Found: {len(results['apiData'])}")
        for item in results['apiData']:
            print(f"\n    {item['path']}:")
            print(f"    {item['sample']}")

        print(f"\n  Window Properties Found: {len(results['dataLayers'])}")
        for item in results['dataLayers'][:10]:  # First 10
            print(f"\n    window.{item['key']} ({item['type']}):")
            print(f"    {item['sample']}")

    except Exception as e:
        print(f"  Error: {e}")


async def explore_data_attributes(page):
    """Find elements with data-* attributes that might contain sources."""
    print("\n" + "="*80)
    print("EXPLORING DATA-* ATTRIBUTES")
    print("="*80)

    js_code = """
    (() => {
        const results = [];
        const allElements = document.querySelectorAll('[data-*]');

        // Get all elements with data attributes
        document.querySelectorAll('*').forEach(el => {
            const dataAttrs = {};
            let hasRelevant = false;

            for (let attr of el.attributes) {
                if (attr.name.startsWith('data-')) {
                    const name = attr.name.toLowerCase();
                    const value = attr.value.toLowerCase();

                    if (name.includes('source') ||
                        name.includes('citation') ||
                        name.includes('reference') ||
                        value.includes('source') ||
                        value.includes('citation')) {

                        hasRelevant = true;
                        dataAttrs[attr.name] = attr.value;
                    }
                }
            }

            if (hasRelevant) {
                results.push({
                    tag: el.tagName,
                    attributes: dataAttrs,
                    text: el.textContent.substring(0, 100),
                    hasLinks: el.querySelectorAll('a').length > 0,
                    linkCount: el.querySelectorAll('a').length
                });
            }
        });

        return results;
    })();
    """

    try:
        results = await page.evaluate(js_code)

        print(f"\n  Found {len(results)} elements with relevant data-* attributes")

        for idx, item in enumerate(results[:10], 1):  # First 10
            print(f"\n  --- Element {idx} ---")
            print(f"    Tag: {item['tag']}")
            print(f"    Data Attributes: {json.dumps(item['attributes'], indent=6)}")
            print(f"    Contains Links: {item['linkCount']} links")
            print(f"    Text: {item['text']}")

    except Exception as e:
        print(f"  Error: {e}")


async def explore_shadow_dom(page):
    """Search shadow DOM for sources."""
    print("\n" + "="*80)
    print("EXPLORING SHADOW DOM")
    print("="*80)

    js_code = """
    (() => {
        const results = [];

        function searchShadowRoots(root, depth = 0) {
            if (depth > 3) return;

            const elements = root.querySelectorAll('*');
            elements.forEach(el => {
                if (el.shadowRoot) {
                    // Found shadow root
                    const links = el.shadowRoot.querySelectorAll('a[href]');
                    if (links.length > 0) {
                        results.push({
                            hostTag: el.tagName,
                            linkCount: links.length,
                            samples: Array.from(links).slice(0, 2).map(a => ({
                                href: a.href,
                                text: a.textContent.substring(0, 50)
                            }))
                        });
                    }

                    // Recurse into shadow DOM
                    searchShadowRoots(el.shadowRoot, depth + 1);
                }
            });
        }

        searchShadowRoots(document);
        return results;
    })();
    """

    try:
        results = await page.evaluate(js_code)

        if len(results) == 0:
            print("  ✗ No shadow DOM elements with links found")
            return

        print(f"  ✓ Found {len(results)} shadow DOM hosts with links")

        for idx, item in enumerate(results, 1):
            print(f"\n  --- Shadow Host {idx} ---")
            print(f"    Host Tag: {item['hostTag']}")
            print(f"    Links Inside: {item['linkCount']}")
            print(f"    Samples:")
            for sample in item['samples']:
                print(f"      - {sample['text']}")
                print(f"        {sample['href']}")

    except Exception as e:
        print(f"  Error: {e}")


async def monitor_network_requests(page):
    """Monitor network requests for API calls that might return source data."""
    print("\n" + "="*80)
    print("MONITORING NETWORK REQUESTS")
    print("="*80)
    print("  (Will monitor for 15 seconds after search is submitted)")

    captured_requests = []

    # Enable network monitoring
    await page.send(cdp.network.enable())

    # Handler for responses
    async def response_handler(event):
        try:
            # Check if response might contain source data
            url = event.response.url
            if any(keyword in url.lower() for keyword in ['api', 'search', 'query', 'answer']):
                captured_requests.append({
                    'url': url,
                    'status': event.response.status,
                    'type': event.response.mime_type
                })
        except:
            pass

    # Listen for responses
    page.add_handler(cdp.network.ResponseReceived, response_handler)

    print("  Network monitoring enabled")
    return captured_requests


async def main():
    print("="*80)
    print("PERPLEXITY SOURCE DATA INVESTIGATION")
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

    # Start network monitoring
    captured_requests = await monitor_network_requests(page)

    # Perform search
    print("\n5. Performing test search...")
    test_query = "What is quantum computing?"

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
        return

    await search_input.click()
    await search_input.send_keys(test_query)
    await asyncio.sleep(0.5)
    await search_input.send_keys('\n')

    # Wait for results
    print("   Waiting for results and monitoring network...")
    await asyncio.sleep(15)

    # Explore all data sources
    await explore_data_attributes(page)
    await explore_react_data(page)
    await explore_window_objects(page)
    await explore_shadow_dom(page)

    # Report network requests
    print("\n" + "="*80)
    print("NETWORK REQUESTS CAPTURED")
    print("="*80)
    print(f"\n  Captured {len(captured_requests)} relevant requests")

    for idx, req in enumerate(captured_requests[:10], 1):
        print(f"\n  Request {idx}:")
        print(f"    URL: {req['url']}")
        print(f"    Status: {req['status']}")
        print(f"    Type: {req['type']}")

    # Keep browser open
    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    print("\nBrowser will remain open for manual DevTools inspection.")
    print("Press Ctrl+C to exit...")

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
