"""
Main search automation script for Perplexity.ai
Authenticates using cookies and performs a search query
"""
import sys
import asyncio
import time
import hashlib
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from functools import wraps
import nodriver as uc
from src.utils.cookies import load_cookies, validate_auth_cookies
from src.utils.storage import save_search_result
from src.config import (
    BROWSER_CONFIG, HUMAN_BEHAVIOR, TIMEOUTS, STABILITY_CONFIG,
    SELECTORS, EXTRACTION_MARKERS, REQUIRED_COOKIES, COOKIE_DEFAULTS,
    RETRY_CONFIG, SCREENSHOT_CONFIG, LOGGING_CONFIG, USER_AGENTS, VIEWPORT_SIZES
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def human_delay(delay_type: str = 'short') -> None:
    """
    Add human-like random delays to avoid detection

    Args:
        delay_type: 'short', 'medium', or 'long'
    """
    delays = HUMAN_BEHAVIOR['delays']

    if delay_type == 'short':
        delay = random.uniform(delays['short_min'], delays['short_max'])
    elif delay_type == 'medium':
        delay = random.uniform(delays['medium_min'], delays['medium_max'])
    elif delay_type == 'long':
        delay = random.uniform(delays['long_min'], delays['long_max'])
    else:
        delay = random.uniform(delays['short_min'], delays['short_max'])

    await asyncio.sleep(delay)


def async_retry(max_attempts: int = None, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying async functions with exponential backoff

    Args:
        max_attempts: Maximum retry attempts (defaults to RETRY_CONFIG)
        exceptions: Tuple of exceptions to catch
    """
    if max_attempts is None:
        max_attempts = RETRY_CONFIG['max_attempts']

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = RETRY_CONFIG['base_delay']
                        if RETRY_CONFIG['exponential']:
                            delay *= (RETRY_CONFIG['backoff_factor'] ** attempt)

                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")

            raise last_exception

        return wrapper
    return decorator


async def find_interactive_element(page, selectors: List[str], timeout: int = None):
    """
    Find an interactive element with visibility and interactability checks

    Args:
        page: Nodriver page object
        selectors: List of CSS selectors to try
        timeout: Timeout for element selection

    Returns:
        Element if found and interactive, None otherwise
    """
    if timeout is None:
        timeout = TIMEOUTS['element_select']

    for selector in selectors:
        try:
            element = await page.select(selector, timeout=timeout)
            if element:
                # Check if element is visible and enabled
                try:
                    # Try to get element properties
                    is_visible = await page.evaluate(
                        f'document.querySelector("{selector}") !== null && '
                        f'window.getComputedStyle(document.querySelector("{selector}")).display !== "none" && '
                        f'window.getComputedStyle(document.querySelector("{selector}")).visibility !== "hidden"'
                    )

                    if is_visible:
                        logger.debug(f"Found interactive element: {selector}")
                        return element
                except:
                    # If we can't check visibility, assume it's visible
                    logger.debug(f"Found element (visibility check skipped): {selector}")
                    return element
        except:
            continue

    return None


async def health_check(page) -> Dict[str, Any]:
    """
    Perform health check on current page state

    Returns:
        Dictionary with health check results
    """
    health = {
        'url': page.url if hasattr(page, 'url') else None,
        'title': None,
        'responsive': False,
        'main_content_present': False,
    }

    try:
        # Check if page is responsive
        try:
            health['title'] = await page.evaluate('document.title')
            health['responsive'] = True
        except:
            pass

        # Check if main content is present
        try:
            main = await page.select('main', timeout=2)
            health['main_content_present'] = main is not None
        except:
            pass

    except Exception as e:
        logger.warning(f"Health check error: {e}")

    return health


async def type_like_human(element, text: str) -> None:
    """
    Type text character-by-character with human-like delays

    Args:
        element: Element to type into
        text: Text to type
    """
    typing_speed = HUMAN_BEHAVIOR['typing_speed']

    for char in text:
        await element.send_keys(char)

        # Longer delay for spaces (more realistic)
        if char == ' ':
            delay = random.uniform(typing_speed['space_min'], typing_speed['space_max'])
        else:
            delay = random.uniform(typing_speed['char_min'], typing_speed['char_max'])

        await asyncio.sleep(delay)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

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

        logger.info('=' * 60)
        logger.info('Perplexity.ai Search Automation')
        logger.info('=' * 60)
        logger.info(f'Query: "{search_query}"')
        if model:
            logger.info(f'Model: {model}')

        # Step 1: Load and validate cookies
        logger.info('Loading authentication cookies...')
        cookies = load_cookies()
        validate_auth_cookies(cookies)

        # Step 2: Launch browser with randomized fingerprint
        logger.info('Launching browser (headed mode with fingerprint randomization)...')

        # Randomize user agent and viewport for bot detection avoidance
        user_agent = random.choice(USER_AGENTS)
        viewport = random.choice(VIEWPORT_SIZES)

        logger.debug(f"Using User-Agent: {user_agent[:50]}...")
        logger.debug(f"Using viewport: {viewport['width']}x{viewport['height']}")

        browser = await uc.start(
            headless=BROWSER_CONFIG['headless'],
            browser_args=BROWSER_CONFIG['args'] + [
                f'--user-agent={user_agent}',
                f'--window-size={viewport["width"]},{viewport["height"]}',
            ]
        )

        # Step 3: Get first page
        page = browser.main_tab

        # Step 4: Set cookies BEFORE navigating
        logger.info('Setting authentication cookies...')
        await set_cookies(page, cookies)
        logger.info('Cookies added to browser')

        # Step 5: Navigate to Perplexity with cookies already set
        logger.info('Navigating to Perplexity.ai...')
        await page.get('https://www.perplexity.ai')
        await human_delay('medium')

        # Perform health check
        health = await health_check(page)
        logger.debug(f"Page health: {health}")

        # Step 6: Verify authentication
        logger.info('Verifying authentication status...')
        is_authenticated = await verify_authentication(page)

        if not is_authenticated:
            raise Exception('Authentication failed - cookies may be expired or invalid')

        logger.info('Successfully authenticated!')

        # Step 7: Perform search
        logger.info('Performing search...')
        await perform_search(page, search_query)

        # Step 8: Wait for and extract results
        logger.info('Waiting for search results...')

        # Generate unique screenshot filename (only if screenshots are enabled)
        screenshot_path = None
        if save_screenshot:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
            screenshot_dir = Path(SCREENSHOT_CONFIG['directory'])
            screenshot_dir.mkdir(exist_ok=True)
            screenshot_path = screenshot_dir / f'{timestamp_str}_{query_hash}.{SCREENSHOT_CONFIG["format"]}'

        results = await extract_search_results(page, str(screenshot_path) if screenshot_path else None)

        # Step 9: Display results
        display_results(results)

        # Step 10: Save to database
        execution_time = time.time() - start_time
        logger.info('Saving results to database...')
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
        logger.info(f'Saved as record ID: {result_id}')
        logger.info(f'Execution time: {execution_time:.2f}s')

    except Exception as error:
        logger.error(f'Error: {str(error)}', exc_info=True)
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
        except Exception as db_error:
            logger.warning(f'Could not save failed result to database: {db_error}')

        raise
    finally:
        # Cleanup
        if browser:
            logger.info('Cleaning up...')
            browser.stop()
            logger.info('Browser closed')


@async_retry(max_attempts=2, exceptions=(Exception,))
async def set_cookies(page, cookies: List[Dict]) -> None:
    """
    Set cookies in the browser page with error handling and verification

    Args:
        page: Nodriver page object
        cookies: List of cookie dictionaries

    Raises:
        Exception: If critical cookies cannot be set
    """
    cookies_set = 0
    critical_cookies_set = 0

    for cookie in cookies:
        try:
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            domain = cookie.get('domain', COOKIE_DEFAULTS['domain'])
            path = cookie.get('path', COOKIE_DEFAULTS['path'])

            if not name or not value:
                logger.warning(f'Skipping invalid cookie (missing name or value)')
                continue

            # Use CDP network.set_cookie with proper parameter handling
            await page.send(uc.cdp.network.set_cookie(
                name=name,
                value=value,
                domain=domain,
                path=path,
                secure=cookie.get('secure', COOKIE_DEFAULTS['secure']),
                http_only=cookie.get('httpOnly', COOKIE_DEFAULTS['httpOnly']),
                same_site=uc.cdp.network.CookieSameSite(
                    cookie.get('sameSite', COOKIE_DEFAULTS['sameSite'])
                ) if cookie.get('sameSite') else None,
                expires=uc.cdp.network.TimeSinceEpoch(cookie['expires'])
                    if cookie.get('expires') and cookie['expires'] > 0 else None
            ))

            cookies_set += 1

            # Track critical cookies
            if name in REQUIRED_COOKIES:
                critical_cookies_set += 1
                logger.debug(f'Set critical cookie: {name}')
            else:
                logger.debug(f'Set cookie: {name}')

        except Exception as e:
            cookie_name = cookie.get('name', 'unknown')
            if cookie_name in REQUIRED_COOKIES:
                logger.error(f'Failed to set critical cookie {cookie_name}: {e}')
                raise  # Fail fast for critical cookies
            else:
                logger.warning(f'Could not set cookie {cookie_name}: {e}')

    logger.info(f'Set {cookies_set} cookies ({critical_cookies_set} critical)')

    # Verify critical cookies were set
    if critical_cookies_set < len(REQUIRED_COOKIES):
        raise Exception(f'Not all critical cookies were set ({critical_cookies_set}/{len(REQUIRED_COOKIES)})')

    # Add small delay to ensure cookies are applied
    await human_delay('short')


async def verify_authentication(page) -> bool:
    """
    Verify that the user is authenticated on Perplexity.ai

    Returns:
        True if authenticated, False otherwise
    """
    try:
        # Wait for page to fully load
        await human_delay('medium')

        # Check for sign-in button (should NOT be present if authenticated)
        try:
            sign_in_elements = await page.select_all('button')
            for btn in sign_in_elements:
                text = btn.text  # .text is a property, not async
                if text and ('Sign In' in text or 'Log In' in text):
                    logger.warning('Found visible "Sign In" button - not authenticated')
                    return False
        except Exception as e:
            logger.debug(f'Sign-in button check failed: {e}')

        # Check for authenticated sidebar elements
        for selector in SELECTORS['auth_indicators']:
            try:
                element = await page.select(selector, timeout=TIMEOUTS['auth_verification'])
                if element:
                    logger.info(f'Found authenticated element: {selector}')
                    return True
            except:
                continue

        # Check for "Account" text in page (another strong indicator)
        try:
            body = await page.select('body')
            if body:
                body_text = body.text_all  # .text_all is a property, no await
                if body_text and 'Account' in body_text and 'Home' in body_text:
                    logger.info('Found "Account" and "Home" navigation - authenticated')
                    return True
        except Exception as e:
            logger.debug(f'Account text check failed: {e}')

        logger.warning('Could not verify authentication - cookies may be expired')
        return False

    except Exception as error:
        logger.error(f'Error during authentication verification: {error}')
        return False


async def perform_search(page, query: str) -> None:
    """
    Perform a search query on Perplexity.ai with human-like behavior

    Args:
        page: Nodriver page object
        query: Search query string
    """
    try:
        # Find search input using helper function
        search_input = await find_interactive_element(
            page,
            SELECTORS['search_input'],
            timeout=TIMEOUTS['element_select']
        )

        if not search_input:
            raise Exception('Could not find search input element')

        logger.info('Found search input')

        # Click to focus the input with human delay
        await search_input.click()
        await human_delay('short')

        # Type the query character-by-character (most realistic)
        logger.info(f'Typing query: "{query}"')
        await type_like_human(search_input, query)
        logger.info('Query entered')

        # Human delay before submitting
        await human_delay('short')

        # Submit the search using triple fallback approach
        # Method 1: Send newline character
        await search_input.send_keys('\n')
        logger.debug('Sent newline character')

        # Wait briefly for initial response
        await human_delay('short')

        # Method 2: Try using CDP to send Enter key event directly
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
            logger.debug('Sent Enter key event via CDP')
        except Exception as e:
            logger.debug(f'CDP Enter key fallback error: {e}')

        # Wait for search to register
        await human_delay('medium')

        # Method 3: Fallback - try clicking search button if Enter didn't work
        try:
            search_button = await find_interactive_element(
                page,
                SELECTORS['search_button'],
                timeout=2
            )

            if search_button:
                logger.debug('Found search button, clicking as fallback')
                await search_button.click()
                await human_delay('short')
        except Exception as e:
            logger.debug(f'Search button fallback not needed: {e}')

        logger.info('Search submitted')

    except Exception as error:
        raise Exception(f'Failed to perform search: {str(error)}')


async def wait_for_content_stability(page, max_wait: int = None) -> bool:
    """
    Wait for answer content to stabilize using multiple indicators

    Args:
        page: Nodriver page object
        max_wait: Maximum time to wait (defaults to STABILITY_CONFIG)

    Returns:
        True if content stabilized, False if timeout
    """
    if max_wait is None:
        max_wait = TIMEOUTS['content_stability']

    logger.info('Waiting for answer to be generated...')

    check_interval = STABILITY_CONFIG['check_interval']
    stable_threshold = STABILITY_CONFIG['stable_threshold']
    min_content_length = STABILITY_CONFIG['min_content_length']

    stable_count = 0
    last_length = 0
    last_hash = ""

    start_time = asyncio.get_event_loop().time()

    while (asyncio.get_event_loop().time() - start_time) < max_wait:
        try:
            # Get main content
            main_content = await page.select('main', timeout=2)
            if not main_content:
                await asyncio.sleep(check_interval)
                continue

            # Use text_all to get full content (no await!)
            current_text = main_content.text_all
            current_length = len(current_text) if current_text else 0

            # Use hash for better change detection (catches small edits)
            current_hash = hashlib.md5(current_text.encode()).hexdigest() if current_text else ""

            # Check if content meets minimum threshold and has stabilized
            if current_length >= min_content_length:
                # Content is substantial, check if stable
                if current_hash == last_hash and current_length == last_length:
                    stable_count += 1
                    if stable_count >= stable_threshold:
                        logger.info(f'Answer generation complete (content stable at {current_length} chars)')
                        return True
                else:
                    # Content changed, reset counter
                    stable_count = 0
                    last_hash = current_hash
                    last_length = current_length
                    logger.debug(f'Content changing: {current_length} chars')
            else:
                # Not enough content yet
                stable_count = 0
                last_hash = current_hash
                last_length = current_length

        except Exception as e:
            logger.debug(f'Stability check error: {e}')

        await asyncio.sleep(check_interval)

    # Timeout reached
    logger.warning(f'Timeout after {max_wait}s, proceeding with current content...')
    return False


async def extract_search_results(page, screenshot_path: Optional[str]) -> Dict:
    """
    Extract search results from the page with multiple fallback strategies

    Args:
        page: Nodriver page object
        screenshot_path: Path to save screenshot (if enabled)

    Returns:
        Dictionary with 'answer' and 'sources' keys
    """
    try:
        logger.info('Checking if search initiated...')

        # First, verify that the search actually started
        search_started = False
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < TIMEOUTS['search_initiation']:
            # Check for URL change (most reliable indicator)
            if page.url and '/search' in page.url:
                search_started = True
                logger.info('Search initiated (detected URL change)')
                break

            # Check for loading indicators from config
            for selector in SELECTORS['loading_indicators']:
                try:
                    element = await page.select(selector, timeout=1)
                    if element:
                        search_started = True
                        logger.info(f'Search initiated (detected: {selector})')
                        break
                except:
                    continue

            if search_started:
                break

            await asyncio.sleep(0.5)

        if not search_started:
            logger.warning('Could not confirm search started, proceeding anyway...')

        # Use improved stability detection
        await wait_for_content_stability(page)

        # Additional short wait to ensure rendering complete
        await human_delay('short')

        logger.info('Extracting results...')

        # Take screenshot for debugging (if enabled)
        if screenshot_path:
            await page.save_screenshot(screenshot_path, full_page=SCREENSHOT_CONFIG['full_page'])
            logger.info(f'Screenshot saved: {screenshot_path}')

        # Extract the main answer/response using multiple strategies
        answer_text = ''

        # Strategy 1: Marker-based extraction (most accurate)
        try:
            await human_delay('medium')  # Ensure content is fully rendered

            main_element = await page.select('main')
            if main_element:
                # Get all text content including children (text_all gets all descendants)
                full_text = main_element.text_all
                logger.debug(f'Full main text length: {len(full_text) if full_text else 0}')

                if full_text:
                    # text_all concatenates with spaces, so we need a different approach
                    # Look for the answer portion between known markers
                    text_lower = full_text.lower()

                    # Find where answer starts
                    start_idx = -1
                    for marker in EXTRACTION_MARKERS['start']:
                        idx = text_lower.find(marker.lower())
                        if idx > 0:
                            start_idx = idx + len(marker)
                            logger.debug(f'Found start marker: {marker}')
                            break

                    # Find where answer ends
                    end_idx = len(full_text)
                    for marker in EXTRACTION_MARKERS['end']:
                        idx = text_lower.find(marker.lower(), start_idx if start_idx > 0 else 0)
                        if idx > 0:
                            end_idx = min(end_idx, idx)
                            logger.debug(f'Found end marker: {marker}')

                    if start_idx > 0 and start_idx < end_idx:
                        answer_text = full_text[start_idx:end_idx].strip()

                        # Clean up any remaining UI elements
                        for ui_elem in EXTRACTION_MARKERS['ui_elements']:
                            answer_text = answer_text.replace(ui_elem, '')

                        answer_text = answer_text.strip()
                        if answer_text:
                            logger.info(f'Strategy 1: Found answer text ({len(answer_text)} chars)')

        except Exception as e:
            logger.warning(f'Strategy 1 extraction error: {e}')

        # Strategy 2: Clean text extraction (fallback)
        if not answer_text:
            try:
                logger.debug('Trying strategy 2: Clean text extraction')
                main_content = await page.select('main')
                if main_content:
                    full_text = main_content.text_all
                    if full_text and len(full_text) > 200:
                        # Remove known UI elements and clean up
                        lines = full_text.split('\n')
                        cleaned_lines = []

                        for line in lines:
                            line = line.strip()
                            if line and not any(pattern in line for pattern in EXTRACTION_MARKERS['skip_patterns']):
                                cleaned_lines.append(line)

                        if cleaned_lines:
                            answer_text = '\n'.join(cleaned_lines)
                            logger.info(f'Strategy 2: Found answer text ({len(answer_text)} chars)')
            except Exception as e:
                logger.warning(f'Strategy 2 extraction error: {e}')

        # Strategy 3: Direct answer container (last resort)
        if not answer_text:
            try:
                logger.debug('Trying strategy 3: Direct answer container')
                answer_selectors = [
                    '[data-testid*="answer"]',
                    '[class*="answer"]',
                    'main article',
                    'main [role="article"]',
                ]

                for selector in answer_selectors:
                    try:
                        element = await page.select(selector, timeout=2)
                        if element:
                            text = element.text_all
                            if text and len(text) > 50:
                                answer_text = text.strip()
                                logger.info(f'Strategy 3: Found answer via {selector} ({len(answer_text)} chars)')
                                break
                    except:
                        continue
            except Exception as e:
                logger.warning(f'Strategy 3 extraction error: {e}')

        # Extract sources/citations
        sources = []
        try:
            source_elements = await page.select_all(SELECTORS['sources'])
            logger.debug(f'Found {len(source_elements)} potential source elements')

            for el in source_elements[:10]:  # Limit to top 10 sources
                try:
                    href = el.attrs.get('href') if hasattr(el, 'attrs') else None
                    text = el.text_all  # .text_all is a property, no await

                    if href and text and len(text.strip()) > 3:
                        sources.append({
                            'url': href,
                            'text': text.strip()
                        })
                except Exception as e:
                    logger.debug(f'Error extracting source: {e}')
                    continue

            logger.info(f'Extracted {len(sources)} sources')
        except Exception as e:
            logger.warning(f'Could not extract sources: {e}')

        return {
            'answer': answer_text or 'No answer text extracted',
            'sources': sources
        }

    except Exception as error:
        logger.error(f'Could not extract complete results: {error}')
        return {
            'answer': 'Failed to extract results - page structure may have changed',
            'sources': []
        }


def display_results(results: Dict) -> None:
    """
    Display search results in a formatted way

    Args:
        results: Dictionary with 'answer' and 'sources' keys
    """
    print('\n' + '=' * 60)
    print('SEARCH RESULTS')
    print('=' * 60 + '\n')

    answer = results.get('answer', 'No answer available')
    print('ANSWER:')
    print('-' * 60)
    print(answer if answer is not None else 'No answer available')
    print()

    sources = results.get('sources', [])
    if sources and isinstance(sources, list) and len(sources) > 0:
        print('SOURCES:')
        print('-' * 60)
        for index, source in enumerate(sources):
            if isinstance(source, dict):
                print(f"{index + 1}. {source.get('text', 'N/A')}")
                print(f"   {source.get('url', 'N/A')}")
                print()

    print('=' * 60 + '\n')


if __name__ == '__main__':
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning('\nInterrupted by user')
        sys.exit(0)
    except Exception as e:
        logger.error(f'\nFatal error: {e}', exc_info=True)
        sys.exit(1)
