#!/usr/bin/env python3
"""
Script to find the correct sources overlay close button.

Problem: There are TWO "10 sources" buttons:
1. Left: In answer text - expands/collapses inline sources (WRONG)
2. Right: In overlay panel - closes the entire overlay (CORRECT)

This script identifies the correct button to click.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG


async def main():
    print("="*80)
    print("FINDING SOURCES OVERLAY CLOSE BUTTON")
    print("="*80)

    # Load cookies and start browser
    print("\n1. Loading cookies and starting browser...")
    cookies = load_cookies()
    browser = await uc.start(browser_args=BROWSER_CONFIG['args'], headless=False)
    page = await browser.get("about:blank")

    # Set cookies
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

    # Navigate and search
    print("\n2. Navigating to Perplexity and performing search...")
    await page.get("https://www.perplexity.ai/")
    await asyncio.sleep(3)

    # Find search input
    search_input = await page.find("textarea", best_match=True, timeout=5)
    if search_input:
        await search_input.click()
        await asyncio.sleep(0.5)

        # Type query
        query = "What is GEO?"
        for char in query:
            await search_input.send_keys(char)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.5)
        await search_input.send_keys('\n')
        print("   Search submitted, waiting for results...")
        await asyncio.sleep(15)

    # Now expand sources to create the overlay
    print("\n3. Expanding sources to create overlay...")
    sources_button = await page.find("sources", best_match=True, timeout=3)
    if sources_button:
        button_text = sources_button.text_all.strip() if sources_button.text_all else ""
        print(f"   Found button: '{button_text}'")
        await sources_button.click()
        print("   Clicked to expand, waiting for overlay...")
        await asyncio.sleep(3)

    # Now find ALL buttons containing "source" text
    print("\n4. Finding ALL elements with 'source' text...")
    js_find_sources = """
    (() => {
        const all = Array.from(document.querySelectorAll('*'));
        const matches = all.filter(el => {
            const text = el.textContent || '';
            return text.toLowerCase().includes('source') && el.children.length < 3;
        }).map((el, idx) => {
            const rect = el.getBoundingClientRect();
            return {
                index: idx,
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 50),
                classes: el.className,
                id: el.id,
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                dataTestid: el.getAttribute('data-testid'),
                position: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                visible: rect.width > 0 && rect.height > 0,
                zIndex: window.getComputedStyle(el).zIndex
            };
        });

        // Sort by x position (left to right)
        matches.sort((a, b) => a.position.x - b.position.x);
        return matches;
    })();
    """

    results = await page.evaluate(js_find_sources)

    print(f"\n   Found {len(results)} elements with 'source' text:\n")

    for item in results:
        print(f"   [{item['index']}] {item['tag']}")
        print(f"       Text: '{item['text']}'")
        print(f"       Position: x={item['position']['x']}, y={item['position']['y']}")
        print(f"       Size: {item['position']['width']}x{item['position']['height']}")
        print(f"       Visible: {item['visible']}")
        print(f"       Z-index: {item['zIndex']}")
        if item['classes']:
            print(f"       Classes: {item['classes']}")
        if item['role']:
            print(f"       Role: {item['role']}")
        if item['ariaLabel']:
            print(f"       Aria-label: {item['ariaLabel']}")
        if item['dataTestid']:
            print(f"       Data-testid: {item['dataTestid']}")
        print()

    # Look for overlay/panel/modal containers
    print("\n5. Looking for overlay/panel/modal containers...")
    js_find_overlay = """
    (() => {
        const keywords = ['overlay', 'modal', 'panel', 'drawer', 'sidebar', 'sources'];
        const all = Array.from(document.querySelectorAll('*'));

        const matches = all.filter(el => {
            const classes = (el.className || '').toLowerCase();
            const id = (el.id || '').toLowerCase();
            const role = (el.getAttribute('role') || '').toLowerCase();
            const testid = (el.getAttribute('data-testid') || '').toLowerCase();

            return keywords.some(kw =>
                classes.includes(kw) ||
                id.includes(kw) ||
                role.includes(kw) ||
                testid.includes(kw)
            );
        }).map(el => {
            const rect = el.getBoundingClientRect();
            return {
                tag: el.tagName,
                classes: el.className,
                id: el.id,
                role: el.getAttribute('role'),
                dataTestid: el.getAttribute('data-testid'),
                position: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                visible: rect.width > 0 && rect.height > 0,
                childCount: el.children.length
            };
        }).filter(el => el.visible && el.position.width > 200);

        return matches;
    })();
    """

    overlays = await page.evaluate(js_find_overlay)
    print(f"   Found {len(overlays)} potential overlay containers:\n")

    for overlay in overlays:
        print(f"   {overlay['tag']}")
        print(f"     Position: x={overlay['position']['x']}, y={overlay['position']['y']}")
        print(f"     Size: {overlay['position']['width']}x{overlay['position']['height']}")
        print(f"     Children: {overlay['childCount']}")
        if overlay['classes']:
            print(f"     Classes: {overlay['classes']}")
        if overlay['id']:
            print(f"     ID: {overlay['id']}")
        if overlay['role']:
            print(f"     Role: {overlay['role']}")
        if overlay['dataTestid']:
            print(f"     Data-testid: {overlay['dataTestid']}")
        print()

    # Look for close buttons in high z-index
    print("\n6. Looking for close/dismiss buttons...")
    js_find_close = """
    (() => {
        const all = Array.from(document.querySelectorAll('button, [role="button"]'));
        const matches = all.map(el => {
            const rect = el.getBoundingClientRect();
            const styles = window.getComputedStyle(el);
            return {
                tag: el.tagName,
                text: el.textContent.trim(),
                ariaLabel: el.getAttribute('aria-label'),
                classes: el.className,
                position: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                zIndex: styles.zIndex,
                visible: rect.width > 0 && rect.height > 0
            };
        }).filter(el => {
            const text = (el.text || '').toLowerCase();
            const aria = (el.ariaLabel || '').toLowerCase();
            const isClose = text.includes('close') || text.includes('dismiss') ||
                           aria.includes('close') || aria.includes('dismiss') ||
                           text.includes('×') || text.includes('✕');
            const isSource = text.includes('source');
            return el.visible && (isClose || isSource);
        });

        matches.sort((a, b) => a.position.x - b.position.x);
        return matches;
    })();
    """

    close_buttons = await page.evaluate(js_find_close)
    print(f"   Found {len(close_buttons)} close/source buttons:\n")

    for btn in close_buttons:
        print(f"   {btn['tag']}")
        print(f"     Text: '{btn['text']}'")
        print(f"     Position: x={btn['position']['x']}, y={btn['position']['y']}")
        print(f"     Z-index: {btn['zIndex']}")
        if btn['ariaLabel']:
            print(f"     Aria-label: {btn['ariaLabel']}")
        if btn['classes']:
            print(f"     Classes: {btn['classes']}")
        print()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nBrowser will remain open for manual inspection.")
    print("Look for:")
    print("  1. The rightmost '10 sources' button (highest x position)")
    print("  2. Elements with high z-index (overlay content)")
    print("  3. Close buttons (×, ✕, 'close', 'dismiss')")
    print("\nPress Ctrl+C to exit...")

    try:
        await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    try:
        uc.loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("\nScript interrupted")
