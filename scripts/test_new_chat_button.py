"""
Test script for the new chat button functionality

This script demonstrates how to use the start_new_chat() function
to click the new chat button on Perplexity.ai
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodriver as uc
from src.utils.cookies import load_cookies
from src.browser.auth import set_cookies
from src.browser.navigation import navigate_to_new_chat


async def test_new_chat_button():
    """Test clicking the new chat button."""
    print("🧪 Testing new chat button functionality...")
    print("=" * 80)

    # Launch browser (must be headed for Perplexity)
    print("\n1. Launching browser...")
    browser = await uc.start(headless=False)
    page = await browser.get("about:blank")

    try:
        # Load and set cookies
        print("\n2. Loading authentication cookies...")
        cookies = load_cookies()
        await set_cookies(page, cookies)

        # Navigate to Perplexity
        print("\n3. Navigating to Perplexity.ai...")
        await page.get("https://www.perplexity.ai")
        await asyncio.sleep(3)  # Wait for page to load

        # Click the new chat button
        print("\n4. Clicking new chat button...")
        success = await navigate_to_new_chat(page, verify=True)

        if success:
            print("✅ New chat button clicked successfully!")
            print("   Page is responsive and ready for a new search")
        else:
            print("⚠️  New chat button clicked but page responsiveness uncertain")

        # Keep browser open for manual inspection
        print("\n" + "=" * 80)
        print("✅ Test complete!")
        print("\nThe browser will stay open for manual inspection.")
        print("Press Ctrl+C when done to close.")

        # Wait for user to inspect
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 Closing browser...")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.stop()


async def test_multiple_new_chats():
    """Test clicking the new chat button multiple times."""
    print("🧪 Testing multiple new chat button clicks...")
    print("=" * 80)

    # Launch browser
    print("\n1. Launching browser...")
    browser = await uc.start(headless=False)
    page = await browser.get("about:blank")

    try:
        # Load and set cookies
        print("\n2. Loading authentication cookies...")
        cookies = load_cookies()
        await set_cookies(page, cookies)

        # Navigate to Perplexity
        print("\n3. Navigating to Perplexity.ai...")
        await page.get("https://www.perplexity.ai")
        await asyncio.sleep(3)

        # Click new chat button 3 times with delays
        num_clicks = 3
        print(f"\n4. Clicking new chat button {num_clicks} times...")

        for i in range(1, num_clicks + 1):
            print(f"\n   Click {i}/{num_clicks}...")
            success = await navigate_to_new_chat(page, verify=True)

            if success:
                print(f"   ✅ Click {i} successful")
            else:
                print(f"   ⚠️  Click {i} completed with warnings")

            # Wait between clicks
            if i < num_clicks:
                print(f"   Waiting 2 seconds before next click...")
                await asyncio.sleep(2)

        print("\n" + "=" * 80)
        print(f"✅ All {num_clicks} clicks completed!")
        print("\nThe browser will stay open for manual inspection.")
        print("Press Ctrl+C when done to close.")

        # Wait for user to inspect
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 Closing browser...")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.stop()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "multiple":
        print("Running multiple clicks test...\n")
        asyncio.run(test_multiple_new_chats())
    else:
        print("Running single click test...")
        print("(Use 'python scripts/test_new_chat_button.py multiple' for multiple clicks)\n")
        asyncio.run(test_new_chat_button())
