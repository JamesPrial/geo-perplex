"""
Main search automation script for Perplexity.ai
Authenticates using cookies and performs a search query
"""
import sys
import argparse
import asyncio
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict

from src.utils.cookies import load_cookies, validate_auth_cookies
from src.utils.storage import save_search_result
from src.utils.json_export import save_result_to_json
from src.config import SCREENSHOT_CONFIG, LOGGING_CONFIG, MODEL_MAPPING

# Import from new modular structure
from src.browser.manager import launch_browser
from src.browser.auth import set_cookies, verify_authentication
from src.browser.interactions import health_check, human_delay
from src.browser.navigation import navigate_to_new_chat
from src.search.executor import perform_search
from src.search.extractor import extract_search_results, ExtractionResult, collapse_sources_if_expanded
from src.search.model_selector import select_model

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments using argparse.

    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Perplexity.ai Search Automation with GEO Research',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python -m src.search_cli\n'
               '  python -m src.search_cli "What is GEO?"\n'
               '  python -m src.search_cli "What is GEO?" --model gpt-4\n'
               '  python -m src.search_cli "What is GEO?" --save-json --json-output-dir ./results'
    )

    parser.add_argument(
        'query',
        nargs='?',
        default='What is Generative Engine Optimization?',
        help='Search query to execute (default: "What is Generative Engine Optimization?")'
    )

    parser.add_argument(
        '--model',
        help='AI model to select (e.g., gpt-4, claude-3, sonar-pro)'
    )

    parser.add_argument(
        '--no-screenshot',
        action='store_true',
        help='Skip screenshot generation'
    )

    parser.add_argument(
        '--save-json',
        action='store_true',
        help='Save search result to JSON file in specified output directory (includes iteration number for multi-query runs)'
    )

    parser.add_argument(
        '--json-output-dir',
        default='exports',
        help='Directory for JSON exports (default: exports)'
    )

    parser.add_argument(
        '--multi-query',
        action='store_true',
        help='Keep browser open after search for multiple queries (requires manual new chat clicks)'
    )

    parser.add_argument(
        '--auto-new-chat',
        action='store_true',
        help='Automatically click new chat button after each search (enables continuous querying)'
    )

    parser.add_argument(
        '--query-count',
        type=int,
        default=1,
        help='Number of queries to execute with --auto-new-chat (default: 1, use 2+ for multiple queries with same search text)'
    )

    return parser.parse_args()


async def execute_single_search_workflow(
    page: Any,  # nodriver Tab - using Any since nodriver isn't typed
    search_query: str,
    model: Optional[str],
    save_screenshot: bool,
    screenshot_dir: Path,
    args: argparse.Namespace,
    iteration: int = 1
) -> Dict[str, Any]:
    """
    Execute a single search workflow including search, extraction, and result saving.

    Args:
        page: Browser page object
        search_query: Query text to search
        model: AI model identifier (or None)
        save_screenshot: Whether to save screenshot
        screenshot_dir: Directory for screenshots
        args: Command line arguments namespace
        iteration: Query iteration number (for unique filenames)

    Returns:
        Dict with keys: success (bool), result_id (int|None), error (str|None), execution_time (float)
    """
    workflow_start_time = time.time()
    success = True
    error_message = None
    result_id = None

    try:
        # Step 1: Perform search
        logger.info('Performing search...')
        await perform_search(page, search_query)

        # Step 2: Wait for and extract results
        logger.info('Waiting for search results...')

        # Generate unique screenshot filename with iteration counter
        screenshot_path = None
        if save_screenshot:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
            screenshot_path = screenshot_dir / f'{timestamp_str}_{query_hash}_iter{iteration}.{SCREENSHOT_CONFIG["format"]}'

        result = await extract_search_results(page, str(screenshot_path) if screenshot_path else None)

        # Step 3: Display results
        display_results(result)

        # Update success status based on extraction result
        success = result.success
        if not result.success:
            error_message = result.error
            logger.warning(f'Extraction failed: {error_message}')

        # Step 4: Save to database
        execution_time = time.time() - workflow_start_time
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

        # Save to JSON if requested
        if args.save_json:
            result_dict = {
                "id": result_id,
                "query": search_query,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "answer_text": result.answer_text,
                "sources": result.sources,
                "screenshot_path": str(screenshot_path) if screenshot_path else None,
                "execution_time_seconds": execution_time,
                "success": success,
                "error_message": error_message,
                "iteration": iteration
            }
            try:
                json_path = save_result_to_json(result_dict, output_dir=args.json_output_dir)
                logger.info(f'Saved result to JSON: {json_path}')
                print(f'\nResult exported to JSON: {json_path}')
            except Exception as e:
                logger.warning(f'Failed to save JSON: {e}')
                print(f'\nWarning: Failed to save JSON: {e}', file=sys.stderr)

        return {
            'success': success,
            'result_id': result_id,
            'error': error_message,
            'execution_time': execution_time
        }

    except Exception as e:
        logger.error(f'Workflow error: {e}', exc_info=True)
        execution_time = time.time() - workflow_start_time
        return {
            'success': False,
            'result_id': None,
            'error': str(e),
            'execution_time': execution_time
        }


async def main():
    """Main search automation function"""
    browser = None
    start_time = time.time()
    success = True
    error_message = None

    try:
        # Parse command line arguments
        args = parse_arguments()
        search_query = args.query
        model = args.model
        save_screenshot = not args.no_screenshot
        save_json = args.save_json
        json_output_dir = args.json_output_dir

        # Validate flag combinations
        if args.query_count > 1 and not args.auto_new_chat:
            logger.error('--query-count requires --auto-new-chat flag')
            logger.error('Use: python -m src.search_cli "query" --auto-new-chat --query-count N')
            sys.exit(1)

        if args.auto_new_chat and args.multi_query:
            logger.warning('Both --auto-new-chat and --multi-query set; using --auto-new-chat mode')

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

        # Step 7: Select AI model if specified
        if model:
            logger.info(f'Selecting AI model: {model}')
            try:
                success = await select_model(page, model)
                if not success:
                    raise RuntimeError(f'Failed to select model: {model}')
                logger.info(f'Successfully selected model: {model}')
            except ValueError as e:
                logger.error(f'Invalid model name: {e}')
                available = list(MODEL_MAPPING.keys())
                logger.error(f'Available models: {", ".join(available)}')
                raise
            except Exception as e:
                logger.error(f'Model selection failed: {e}')
                raise

        # Step 8: Prepare screenshot directory
        screenshot_dir = Path(SCREENSHOT_CONFIG['directory'])
        screenshot_dir.mkdir(exist_ok=True)

        # Step 9: Execute first search workflow
        workflow_result = await execute_single_search_workflow(
            page=page,
            search_query=search_query,
            model=model,
            save_screenshot=save_screenshot,
            screenshot_dir=screenshot_dir,
            args=args,
            iteration=1
        )

        # Update success and error_message from workflow result
        success = workflow_result['success']
        error_message = workflow_result['error']

        # Step 10: Handle multi-query loop with auto-new-chat
        if args.auto_new_chat and args.query_count > 1:
            remaining_queries = args.query_count - 1
            logger.info(f'\n{"="*60}')
            logger.info(f'AUTO-NEW-CHAT: Executing {remaining_queries} additional queries')
            logger.info(f'{"="*60}\n')

            loop_start_time = time.time()

            for i in range(remaining_queries):
                iteration_num = i + 2
                logger.info(f'\n{"="*60}')
                logger.info(f'--- Starting Query {iteration_num}/{args.query_count} ---')
                logger.info(f'{"="*60}\n')

                # Store current URL for independent verification
                previous_url = page.url
                logger.debug(f"Current URL before navigation: {previous_url}")

                # Close sources panel before navigating to new chat to avoid DOM pollution
                logger.debug("Closing sources panel before new chat...")
                collapse_result = await collapse_sources_if_expanded(page)
                if collapse_result:
                    logger.info("✓ Sources panel collapsed before new chat")
                else:
                    logger.debug("Sources panel already closed or not found")

                # Navigate to new chat
                try:
                    nav_success = await navigate_to_new_chat(
                        page,
                        verify=True,
                        previous_url=previous_url  # Pass for enhanced verification
                    )

                    if not nav_success:
                        # Navigation failure indicates browser/UI issue - stop all remaining queries
                        logger.error(f'Failed to navigate to new chat for query {iteration_num}')
                        logger.error('Navigation verification returned False')
                        logger.error('Stopping multi-query execution')
                        break

                    # INDEPENDENT VERIFICATION: Check URL actually changed
                    current_url = page.url
                    logger.debug(f"Current URL after navigation: {current_url}")

                    if current_url == previous_url:
                        logger.error(f'Navigation claimed success but URL did not change!')
                        logger.error(f'  Previous URL: {previous_url}')
                        logger.error(f'  Current URL:  {current_url}')
                        logger.error(f'This indicates navigation verification gave false positive')
                        logger.error('Stopping multi-query execution to prevent duplicate searches on same page')
                        break

                    logger.info(f'URL changed to new chat page')
                    logger.debug(f'  New URL: {current_url}')

                except Exception as e:
                    # Critical navigation error - cannot continue
                    logger.error(f'Navigation error for query {iteration_num}: {e}')
                    logger.error('Stopping multi-query execution')
                    break

                # Re-select model if specified (UI resets after new chat)
                if model:
                    logger.info(f'Re-selecting model: {model}')
                    try:
                        # type: ignore[arg-type] - page is Any type from nodriver, select_model expects NodriverPage protocol
                        await select_model(page, model)
                        logger.info(f'Model {model} selected for query {iteration_num}')
                    except Exception as e:
                        logger.error(f'Failed to select model {model}: {e}')
                        logger.error('Stopping multi-query execution')
                        break

                # Small delay before next search
                await human_delay('short')

                # Execute search workflow
                logger.info(f'Executing search workflow for query {iteration_num}...')
                try:
                    workflow_result = await execute_single_search_workflow(
                        page=page,
                        search_query=search_query,
                        model=model,  # Reuse selected model
                        save_screenshot=save_screenshot,
                        screenshot_dir=screenshot_dir,
                        args=args,
                        iteration=iteration_num
                    )

                    elapsed = time.time() - loop_start_time
                    if workflow_result['success']:
                        logger.info(f'Query {iteration_num}/{args.query_count} completed successfully ({elapsed:.1f}s total elapsed)')
                    else:
                        logger.warning(f'Query {iteration_num}/{args.query_count} completed with issues: {workflow_result.get("error", "Unknown error")} ({elapsed:.1f}s total elapsed)')

                except Exception as e:
                    # Workflow error - log and continue to next query
                    # This allows collecting partial results even if individual queries fail
                    logger.error(f'Query {iteration_num}/{args.query_count} failed with error: {e}')
                    # Continue to next iteration to attempt remaining queries

            total_elapsed = time.time() - loop_start_time
            logger.info(f'\nCompleted all {args.query_count} queries in {total_elapsed:.1f}s')

        elif args.multi_query:
                logger.info('Multi-query mode: Browser will remain open')
                logger.info('You can manually click the new chat button and perform more searches')
                logger.info('Press Ctrl+C when done')

                # Keep browser alive until user interrupts
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info('User interrupted, closing browser...')

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
            await browser.stop()
            logger.info('Browser closed')


def display_results(result) -> None:
    """
    Display search results in a formatted way

    Args:
        result: ExtractionResult object OR dict with answer/sources keys (for backward compatibility)
    """
    # Normalize input - handle both dict and ExtractionResult for backward compatibility
    if isinstance(result, dict):
        # Legacy dict format from tests
        success = result.get('success', True)
        answer_text = result.get('answer', result.get('answer_text', ''))
        sources = result.get('sources', [])
        strategy_used = result.get('strategy_used')
        error = result.get('error')
    else:
        # ExtractionResult object
        success = result.success
        answer_text = result.answer_text
        sources = result.sources
        strategy_used = result.strategy_used
        error = result.error

    print('\n' + '=' * 60)
    print('📊 SEARCH RESULTS')
    print('=' * 60 + '\n')

    # Show extraction status
    status_symbol = '✓' if success else '✗'
    print(f'Status: {status_symbol} {"Success" if success else "Failed"}')
    if strategy_used:
        print(f'Strategy: {strategy_used}')
    if error:
        print(f'Error: {error}')
    print()

    # Show answer
    print('ANSWER:')
    print('-' * 60)
    print(answer_text if answer_text else 'No answer available')
    print()

    # Show sources
    if sources and len(sources) > 0:
        print('SOURCES:')
        print('-' * 60)
        for index, source in enumerate(sources):
            if isinstance(source, dict):
                # Get domain - either from new field or extract from URL
                domain = source.get('domain', '')
                if not domain and source.get('url'):
                    from urllib.parse import urlparse
                    try:
                        domain = urlparse(source.get('url', '')).netloc
                    except (ValueError, TypeError, AttributeError):
                        domain = ''

                # Get citation number (use original if available, otherwise use index+1)
                citation_num = source.get('citation_number', index + 1)

                # Format: "citation_number. Title [domain]"
                text = source.get('text', 'N/A')
                domain_str = f" [{domain}]" if domain else ""
                print(f"{citation_num}. {text}{domain_str}")
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