"""
Main search automation script for Perplexity.ai
Authenticates using cookies and performs a search query
"""
import sys
import asyncio
from typing import List, Dict, Optional
import nodriver as uc
from src.utils.cookies import load_cookies, validate_auth_cookies


async def main():
    """Main search automation function"""
    browser = None

    try:
        # Get search query from command line arguments
        search_query = sys.argv[1] if len(sys.argv) > 1 else 'What is Generative Engine Optimization?'
        print('\n🔍 Perplexity.ai Search Automation')
        print('================================\n')
        print(f'Query: "{search_query}"\n')

        # Step 1: Load and validate cookies
        print('📋 Loading authentication cookies...')
        cookies = load_cookies()
        validate_auth_cookies(cookies)

        # Step 2: Launch browser
        # Note: Perplexity detects headless mode, so we run with UI visible
        print('\n🚀 Launching browser (headed mode)...')
        browser = await uc.start(
            headless=False,  # Must be False - Perplexity blocks headless browsers
            browser_args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Step 3: Get first page
        page = browser.main_tab

        # Step 4: Set cookies BEFORE navigating
        print('🔐 Setting authentication cookies...')
        await set_cookies(page, cookies)
        print('✓ Cookies added to browser')

        # Step 5: Navigate to Perplexity with cookies already set
        print('🌐 Navigating to Perplexity.ai...')
        await page.get('https://www.perplexity.ai')
        await asyncio.sleep(3)

        # Step 5: Verify authentication
        print('🔑 Verifying authentication status...')
        is_authenticated = await verify_authentication(page)

        if not is_authenticated:
            raise Exception('Authentication failed - cookies may be expired or invalid')

        print('✓ Successfully authenticated!\n')

        # Step 6: Perform search
        print('🔎 Performing search...')
        await perform_search(page, search_query)

        # Step 7: Wait for and extract results
        print('⏳ Waiting for search results...\n')
        results = await extract_search_results(page)

        # Step 8: Display results
        display_results(results)

    except Exception as error:
        print(f'\n❌ Error: {str(error)}')
        raise
    finally:
        # Cleanup
        if browser:
            print('\n🧹 Cleaning up...')
            browser.stop()
            print('✓ Browser closed\n')


async def set_cookies(page, cookies: List[Dict]) -> None:
    """Set cookies in the browser page"""
    for cookie in cookies:
        try:
            # Use nodriver's browser context to set cookies
            # The browser.cookies.set_all method expects a list of dicts
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            domain = cookie.get('domain', '.perplexity.ai')
            path = cookie.get('path', '/')

            # Build cookie params
            params = {
                'name': name,
                'value': value,
                'domain': domain,
                'path': path,
            }

            # Add optional fields
            if cookie.get('secure'):
                params['secure'] = True
            if cookie.get('httpOnly'):
                params['httpOnly'] = True
            if 'sameSite' in cookie and cookie['sameSite']:
                params['sameSite'] = cookie['sameSite']
            if 'expires' in cookie and cookie['expires'] and cookie['expires'] > 0:
                params['expires'] = cookie['expires']

            # Use CDP network.set_cookie directly with properly formatted params
            await page.send(uc.cdp.network.set_cookie(
                name=name,
                value=value,
                domain=domain,
                path=path,
                secure=cookie.get('secure', False),
                http_only=cookie.get('httpOnly', False),
                same_site=uc.cdp.network.CookieSameSite(cookie.get('sameSite', 'Lax')) if cookie.get('sameSite') else None,
                expires=uc.cdp.network.TimeSinceEpoch(cookie['expires']) if cookie.get('expires') and cookie['expires'] > 0 else None
            ))
        except Exception as e:
            print(f'⚠ Warning: Could not set cookie {cookie.get("name")}: {e}')


async def verify_authentication(page) -> bool:
    """Verify that the user is authenticated on Perplexity.ai"""
    try:
        # Wait a moment for the page to fully load
        await asyncio.sleep(3)

        # Check for sign-in button (should NOT be present if authenticated)
        try:
            sign_in_elements = await page.select_all('button')
            for btn in sign_in_elements:
                text = await btn.text
                if text and ('Sign In' in text or 'Log In' in text):
                    print('⚠ Found visible "Sign In" button - not authenticated')
                    return False
        except:
            pass

        # Check for authenticated sidebar elements
        auth_indicators = [
            '[data-testid="sidebar-new-thread"]',  # New Thread button
            '[data-testid="sidebar-home"]',         # Home navigation
            '[aria-label="New Thread"]',            # New Thread button by aria-label
            '[aria-label="Account"]',               # Account button
        ]

        for selector in auth_indicators:
            try:
                element = await page.select(selector)
                if element:
                    print(f'✓ Found authenticated element: {selector}')
                    return True
            except:
                continue

        # Check for "Account" text in page (another strong indicator)
        try:
            body = await page.select('body')
            body_text = await body.text
            if body_text and 'Account' in body_text and 'Home' in body_text:
                print('✓ Found "Account" and "Home" navigation - authenticated')
                return True
        except:
            pass

        print('⚠ Could not verify authentication - cookies may be expired')
        return False

    except Exception as error:
        print(f'Error during authentication verification: {error}')
        return False


async def perform_search(page, query: str) -> None:
    """Perform a search query on Perplexity.ai"""
    try:
        # Perplexity uses a contenteditable div or textarea for input
        # Try multiple selectors to find the search input
        search_input_selectors = [
            '[contenteditable="true"]',
            'textarea[placeholder*="Ask"]',
            '[role="textbox"]',
            'div[contenteditable="true"]',
            'textarea',
        ]

        search_input = None
        used_selector = ''

        for selector in search_input_selectors:
            try:
                await asyncio.sleep(1)
                search_input = await page.select(selector)
                if search_input:
                    used_selector = selector
                    break
            except:
                continue

        if not search_input:
            raise Exception('Could not find search input element')

        print(f'✓ Found search input: {used_selector}')

        # Click to focus the input
        await search_input.click()
        await asyncio.sleep(0.5)

        # Type the query
        await search_input.send_keys(query)
        print(f'✓ Query entered: "{query}"')

        # Submit the search (press Enter)
        await search_input.send_keys('\n')
        print('✓ Search submitted')

    except Exception as error:
        raise Exception(f'Failed to perform search: {str(error)}')


async def extract_search_results(page) -> Dict:
    """Extract search results from the page"""
    try:
        print('   Waiting for answer to be generated...')

        # Simple approach: wait a fixed time for results to generate
        # Perplexity typically takes 10-30 seconds to generate answers
        await asyncio.sleep(20)

        print('   ✓ Extracting results...')

        # Take screenshot for debugging
        await page.save_screenshot('search-results-screenshot.png', full_page=True)

        # Extract the main answer/response
        answer_text = ''

        # Method 1: Try to get all text from main content area
        try:
            main_content = await page.select('main')
            if main_content:
                full_text = await main_content.text
                if full_text:
                    # Remove navigation/UI text
                    cleaned = full_text
                    cleaned = cleaned.replace('HomeHomeDiscoverSpacesFinance', '')
                    cleaned = cleaned.replace('Install', '')
                    cleaned = cleaned.replace('Ask a follow-up', '')
                    cleaned = cleaned.replace('Answer', '')
                    cleaned = cleaned.replace('Thinking...', '')
                    cleaned = cleaned.strip()

                    if len(cleaned) > 50:
                        answer_text = cleaned
        except:
            pass

        # Method 2: If that didn't work, try answer container
        if not answer_text or len(answer_text) < 50:
            try:
                answer_containers = await page.select_all('[data-testid*="answer"]')
                for container in answer_containers:
                    container_text = await container.text
                    if container_text and len(container_text) > 20:
                        answer_text = container_text
                        answer_text = answer_text.replace('Answer', '')
                        answer_text = answer_text.replace('Thinking...', '')
                        answer_text = answer_text.strip()
                        break
            except:
                pass

        # Extract sources/citations
        sources = []
        try:
            source_elements = await page.select_all('[data-testid*="source"] a, footer a[href*="http"]')
            for el in source_elements[:10]:
                try:
                    href = await el.get_attribute('href')
                    text = await el.text
                    if href and text and len(text.strip()) > 3:
                        sources.append({
                            'url': href,
                            'text': text.strip()
                        })
                except:
                    continue
        except:
            pass

        return {
            'answer': answer_text or 'No answer text extracted',
            'sources': sources
        }

    except Exception as error:
        print(f'Warning: Could not extract complete results: {error}')
        return {
            'answer': 'Failed to extract results - page structure may have changed',
            'sources': []
        }


def display_results(results: Dict) -> None:
    """Display search results in a formatted way"""
    print('═══════════════════════════════════════════════════════════')
    print('📊 SEARCH RESULTS')
    print('═══════════════════════════════════════════════════════════\n')

    print('ANSWER:')
    print('-------')
    print(results['answer'])
    print()

    if len(results['sources']) > 0:
        print('\nSOURCES:')
        print('--------')
        for index, source in enumerate(results['sources']):
            print(f"{index + 1}. {source['text']}")
            print(f"   {source['url']}")

    print('\n═══════════════════════════════════════════════════════════')


if __name__ == '__main__':
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\n⚠ Interrupted by user')
        sys.exit(0)
    except Exception as e:
        print(f'\n💥 Fatal error: {e}')
        sys.exit(1)
