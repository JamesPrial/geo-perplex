"""
Main search automation script for Perplexity.ai
Authenticates using cookies and performs a search query
"""
import sys
import asyncio
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from src.utils.cookies import load_cookies, validate_auth_cookies
from src.utils.storage import save_search_result
from src.config import SCREENSHOT_CONFIG, LOGGING_CONFIG

# Import from new modular structure
from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.browser.interactions import health_check, human_delay
from src.search.executor import perform_search
from src.search.extractor import extract_search_results, ExtractionResult

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


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
        browser = await launch_browser()

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

        result = await extract_search_results(page, str(screenshot_path) if screenshot_path else None)

        # Step 9: Display results
        display_results(result)

        # Update success status based on extraction result
        success = result.success
        if not result.success:
            error_message = result.error
            logger.warning(f'Extraction failed: {error_message}')

        # Step 10: Save to database
        execution_time = time.time() - start_time
        logger.info('Saving results to database...')
        result_id = save_search_result(
            query=search_query,
            answer_text=result.answer_text,
            sources=result.sources,
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            model=model,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        logger.info(f'Saved as record ID: {result_id}')
        logger.info(f'Execution time: {execution_time:.2f}s')
        if result.strategy_used:
            logger.info(f'Extraction strategy: {result.strategy_used}')
        logger.info(f'Extraction time: {result.extraction_time:.2f}s')

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


def display_results(result: ExtractionResult) -> None:
    """
    Display search results in a formatted way

    Args:
        result: ExtractionResult object with answer, sources, and metadata
    """
    print('\n' + '=' * 60)
    print('SEARCH RESULTS')
    print('=' * 60 + '\n')

    # Show extraction status
    status_symbol = '✓' if result.success else '✗'
    print(f'Status: {status_symbol} {"Success" if result.success else "Failed"}')
    if result.strategy_used:
        print(f'Strategy: {result.strategy_used}')
    if result.error:
        print(f'Error: {result.error}')
    print()

    # Show answer
    print('ANSWER:')
    print('-' * 60)
    print(result.answer_text if result.answer_text else 'No answer available')
    print()

    # Show sources
    if result.sources and len(result.sources) > 0:
        print('SOURCES:')
        print('-' * 60)
        for index, source in enumerate(result.sources):
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