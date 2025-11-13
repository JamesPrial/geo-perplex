#!/usr/bin/env python3
"""
Quick diagnostic to see what elements are on the Perplexity page.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
import nodriver.cdp as cdp
from src.utils.cookies import load_cookies
from src.config import BROWSER_CONFIG


async def main():
    print("PERPLEXITY PAGE DIAGNOSTIC")
    print("=" * 80)

    # Load cookies
    print("\n1. Loading cookies...")
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

    # Navigate
    print("\n4. Navigating to Perplexity...")
    await page.get("https://www.perplexity.ai/")
    print("   Waiting 10 seconds for page to fully load...")
    await asyncio.sleep(10)  # Wait for JavaScript to render

    # Get page title
    print("\n5. Page diagnostics...")
    title = await page.evaluate("document.title")
    print(f"   Page title: {title}")

    # Check for textareas
    print("\n6. Looking for textareas...")
    textareas_js = """
    (() => {
        const textareas = document.querySelectorAll('textarea');
        return Array.from(textareas).map(ta => ({
            placeholder: ta.placeholder,
            id: ta.id,
            name: ta.name,
            class: ta.className,
            visible: ta.offsetParent !== null
        }));
    })();
    """
    textareas = await page.evaluate(textareas_js)
    if textareas:
        print(f"   Found {len(textareas)} textarea elements:")
        for idx, ta in enumerate(textareas, 1):
            print(f"     {idx}. placeholder='{ta.get('placeholder', '')}' id='{ta.get('id', '')}' visible={ta.get('visible', False)}")
    else:
        print("   ✗ No textarea elements found!")

    # Check for input elements
    print("\n7. Looking for input elements...")
    inputs_js = """
    (() => {
        const inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
        return Array.from(inputs).map(inp => ({
            placeholder: inp.placeholder,
            id: inp.id,
            name: inp.name,
            type: inp.type,
            class: inp.className,
            visible: inp.offsetParent !== null
        }));
    })();
    """
    inputs = await page.evaluate(inputs_js)
    if inputs:
        print(f"   Found {len(inputs)} input elements:")
        for idx, inp in enumerate(inputs, 1):
            print(f"     {idx}. type='{inp.get('type', '')}' placeholder='{inp.get('placeholder', '')}' id='{inp.get('id', '')}' visible={inp.get('visible', False)}")
    else:
        print("   No relevant input elements found")

    # Check for any element with "ask" in placeholder
    print("\n8. Looking for elements with 'ask' in placeholder/aria-label...")
    ask_elements_js = """
    (() => {
        const all = document.querySelectorAll('*');
        const matches = [];
        all.forEach(el => {
            const placeholder = el.getAttribute('placeholder');
            const ariaLabel = el.getAttribute('aria-label');
            if ((placeholder && placeholder.toLowerCase().includes('ask')) ||
                (ariaLabel && ariaLabel.toLowerCase().includes('ask'))) {
                matches.push({
                    tag: el.tagName,
                    placeholder: placeholder,
                    ariaLabel: ariaLabel,
                    id: el.id,
                    class: el.className,
                    visible: el.offsetParent !== null
                });
            }
        });
        return matches;
    })();
    """
    ask_elements = await page.evaluate(ask_elements_js)
    if ask_elements:
        print(f"   Found {len(ask_elements)} elements with 'ask':")
        for idx, el in enumerate(ask_elements[:10], 1):  # First 10
            print(f"     {idx}. <{el['tag']}> placeholder='{el.get('placeholder', '')}' aria-label='{el.get('ariaLabel', '')}' visible={el.get('visible', False)}")
    else:
        print("   No elements with 'ask' found")

    # Check if we're on a login/signup page
    print("\n9. Checking authentication state...")
    signin_check_js = """
    (() => {
        const signInButtons = Array.from(document.querySelectorAll('button, a')).filter(el =>
            el.textContent && (
                el.textContent.toLowerCase().includes('sign in') ||
                el.textContent.toLowerCase().includes('log in') ||
                el.textContent.toLowerCase().includes('sign up')
            )
        );
        return {
            foundSignIn: signInButtons.length > 0,
            count: signInButtons.length,
            examples: signInButtons.slice(0, 3).map(btn => btn.textContent.trim())
        };
    })();
    """
    try:
        signin_check = await page.evaluate(signin_check_js)
        if signin_check['foundSignIn']:
            print(f"   ⚠ Warning: Found {signin_check['count']} sign-in/signup buttons")
            print(f"   Examples: {signin_check['examples']}")
            print("   This suggests you may not be properly authenticated!")
        else:
            print("   ✓ No sign-in buttons found (likely authenticated)")
    except Exception as e:
        print(f"   Error checking auth state: {e}")

    # Dump some page HTML
    print("\n10. Sample page HTML (body start)...")
    body_html_js = """
    (() => {
        const body = document.body;
        if (!body) return "No body element";
        return body.innerHTML.substring(0, 2000);
    })();
    """
    try:
        body_html = await page.evaluate(body_html_js)
        print(f"   {body_html[:500]}...")
    except Exception as e:
        print(f"   Error getting HTML: {e}")

    print("\n" + "=" * 80)
    print("Browser will remain open for manual inspection.")
    print("Press Ctrl+C to exit...")
    print("=" * 80)

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
