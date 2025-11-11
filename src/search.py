"""
Main search automation script for Perplexity.ai
Authenticates using cookies and performs a search query
"""
import sys
import asyncio
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import nodriver as uc
from src.utils.cookies import load_cookies, validate_auth_cookies
from src.utils.storage import save_search_result


async def main():
    """Main search automation function"""
    browser = None
    start_time = time.time()
    success = True
    error_message = None

    try:
        # Parse command line arguments
        # Usage: python -m src.search "query" [--model MODEL] [--no-screenshot]
        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True  # Default: save screenshots

        # Simple argument parsing
        args = sys.argv[1:]
        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        print('\n🔍 Perplexity.ai Search Automation')
        print('================================\n')
        print(f'Query: "{search_query}"')
        if model:
            print(f'Model: {model}')
        print()

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

        # Generate unique screenshot filename (only if screenshots are enabled)
        screenshot_path = None
        if save_screenshot:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
            screenshot_dir = Path('screenshots')
            screenshot_dir.mkdir(exist_ok=True)
            screenshot_path = screenshot_dir / f'{timestamp_str}_{query_hash}.png'

        results = await extract_search_results(page, str(screenshot_path) if screenshot_path else None)

        # Step 8: Display results
        display_results(results)

        # Step 9: Save to database
        execution_time = time.time() - start_time
        print(f'\n💾 Saving results to database...')
        result_id = save_search_result(
            query=search_query,
            answer_text=results['answer'],
            sources=results['sources'],
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            model=model,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        print(f'✓ Saved as record ID: {result_id}')
        print(f'✓ Execution time: {execution_time:.2f}s')

    except Exception as error:
        print(f'\n❌ Error: {str(error)}')
        success = False
        error_message = str(error)

        # Save failed result to database
        execution_time = time.time() - start_time
        try:
            save_search_result(
                query=search_query if 'search_query' in locals() else 'Unknown',
                answer_text='',
                sources=[],
                screenshot_path=None,
                model=model if 'model' in locals() else None,
                execution_time=execution_time,
                success=False,
                error_message=error_message
            )
        except:
            pass  # Don't fail if database save fails

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

        # Submit the search (press Enter key)
        # First try regular newline
        await search_input.send_keys('\n')
        print('✓ Sent newline character')

        # Alternative: Try using CDP to send Enter key event directly
        try:
            await page.send(uc.cdp.input_.dispatch_key_event(
                type_='keyDown',
                key='Enter',
                code='Enter',
                windows_virtual_key_code=13,
                native_virtual_key_code=13
            ))
            await page.send(uc.cdp.input_.dispatch_key_event(
                type_='keyUp',
                key='Enter',
                code='Enter',
                windows_virtual_key_code=13,
                native_virtual_key_code=13
            ))
            print('✓ Sent Enter key event via CDP')
        except Exception as e:
            print(f'   CDP Enter key fallback: {e}')

        # Wait for search to register
        await asyncio.sleep(1.5)

        # Fallback: Try clicking search button if Enter didn't work
        try:
            # Look for search/submit button
            search_button_selectors = [
                'button[type="submit"]',
                'button[aria-label*="search" i]',
                'button[aria-label*="submit" i]',
                'button[title*="search" i]',
                'button svg',  # Sometimes the search icon is in a button
                'button[class*="search" i]'
            ]

            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = await page.select(selector, timeout=2)
                    if search_button:
                        print(f'   Found search button with selector: {selector}')
                        await search_button.click()
                        print('   ✓ Clicked search button as fallback')
                        break
                except:
                    continue

        except Exception as e:
            # Fallback failed, but that's OK if Enter worked
            print(f'   Note: Search button fallback not needed or not found')

        print('✓ Search submitted')

    except Exception as error:
        raise Exception(f'Failed to perform search: {str(error)}')


async def extract_search_results(page, screenshot_path: Optional[str]) -> Dict:
    """Extract search results from the page"""
    try:
        print('   Checking if search initiated...')

        # First, verify that the search actually started
        # Look for loading indicators
        max_wait_for_start = 10  # seconds
        search_started = False
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < max_wait_for_start:
            # Check for various indicators that search has started
            indicators = [
                # URL change
                lambda: page.url and '/search' in page.url,
                # Loading text
                lambda: page.select('[class*="thinking" i]', timeout=1),
                lambda: page.select('[class*="loading" i]', timeout=1),
                lambda: page.select('[class*="generating" i]', timeout=1),
                # Spinner or animation
                lambda: page.select('[class*="spinner" i]', timeout=1),
                lambda: page.select('[class*="animate" i]', timeout=1),
                # Answer container appearing (even if empty)
                lambda: page.select('[data-testid*="answer"]', timeout=1),
                lambda: page.select('main [class*="response" i]', timeout=1)
            ]

            for check in indicators:
                try:
                    result = await check()
                    if result:
                        search_started = True
                        print(f'   ✓ Search initiated (detected indicator)')
                        break
                except:
                    continue

            if search_started:
                break

            await asyncio.sleep(0.5)

        if not search_started:
            print('   ⚠ Warning: Could not confirm search started, proceeding anyway...')

        print('   Waiting for answer to be generated...')

        # Now wait for the answer to be fully generated
        # Use a smarter approach: wait until content stabilizes
        max_wait_time = 30  # Maximum seconds to wait
        check_interval = 2  # Check every 2 seconds
        stable_checks = 0
        last_content_length = 0

        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            # Check if there's content and if it's stable
            try:
                main_content = await page.select('main', timeout=2)
                if main_content:
                    current_text = await main_content.text
                    current_length = len(current_text) if current_text else 0

                    # Check if content has stabilized (no change for 2 checks)
                    if current_length > 100 and current_length == last_content_length:
                        stable_checks += 1
                        if stable_checks >= 2:
                            print(f'   ✓ Answer generation complete (content stable)')
                            break
                    else:
                        stable_checks = 0
                        last_content_length = current_length
            except:
                pass

            await asyncio.sleep(check_interval)

        # Additional short wait to ensure everything is rendered
        await asyncio.sleep(2)

        print('   ✓ Extracting results...')

        # Take screenshot for debugging (if enabled)
        if screenshot_path:
            await page.save_screenshot(screenshot_path, full_page=True)
            print(f'   📸 Screenshot saved: {screenshot_path}')

        # Extract the main answer/response
        answer_text = ''

        # Method 1: Simple approach - get all text from main and clean it
        try:
            # Wait a bit more for content to fully render
            await asyncio.sleep(3)

            main_element = await page.select('main')
            if main_element:
                # Get all text content including children (text_all gets all descendants)
                full_text = main_element.text_all
                print(f'   Debug: Full main text length: {len(full_text) if full_text else 0}')

                if full_text:
                    # text_all concatenates with spaces, so we need a different approach
                    # Look for the answer portion between known markers
                    text_lower = full_text.lower()

                    # Find where answer starts (after "1 step completed" or "answer images")
                    start_idx = -1
                    start_markers = ['1 step completed', 'answer images', 'images ']
                    for marker in start_markers:
                        idx = text_lower.find(marker)
                        if idx > 0:
                            start_idx = idx + len(marker)
                            break

                    # Find where answer ends (before "ask a follow-up")
                    end_idx = len(full_text)
                    end_markers = ['ask a follow-up', 'ask follow-up']
                    for marker in end_markers:
                        idx = text_lower.find(marker, start_idx if start_idx > 0 else 0)
                        if idx > 0:
                            end_idx = min(end_idx, idx)

                    if start_idx > 0 and start_idx < end_idx:
                        answer_text = full_text[start_idx:end_idx].strip()

                        # Clean up any remaining UI elements
                        ui_elements = ['Home Discover', 'Spaces Finance', 'Upgrade Install', 'Answer Images']
                        for ui_elem in ui_elements:
                            answer_text = answer_text.replace(ui_elem, '')

                        answer_text = answer_text.strip()
                        if answer_text:
                            print(f'   Found answer text ({len(answer_text)} chars)')


        except Exception as e:
            print(f'   Error extracting answer: {e}')

        # Method 2: If no answer found, try getting all text from main
        if not answer_text:
            try:
                main_content = await page.select('main')
                if main_content:
                    full_text = main_content.text_all
                    if full_text and len(full_text) > 200:
                        # Remove known UI elements and clean up
                        lines = full_text.split('\n')
                        cleaned_lines = []
                        skip_patterns = ['Home', 'Discover', 'Spaces', 'Finance', 'Install',
                                       'Upgrade', 'Account', 'Ask a follow-up', 'Thinking...']

                        for line in lines:
                            line = line.strip()
                            if line and not any(pattern in line for pattern in skip_patterns):
                                cleaned_lines.append(line)

                        if cleaned_lines:
                            answer_text = '\n'.join(cleaned_lines)
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
