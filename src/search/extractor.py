"""
Result extraction module for Perplexity.ai search automation

This module handles extracting search results from the page using multiple
fallback strategies to ensure reliability even when UI structure changes.
"""
import asyncio
import logging
from typing import Dict, Optional

from src.config import EXTRACTION_MARKERS, SELECTORS, TIMEOUTS, SCREENSHOT_CONFIG
from src.browser.interactions import human_delay
from src.search.executor import wait_for_content_stability

logger = logging.getLogger(__name__)


async def extract_search_results(page, screenshot_path: Optional[str]) -> Dict:
    """
    Extract search results from the page with multiple fallback strategies

    This function implements a 3-tier extraction strategy:
    1. Marker-based extraction (most accurate) - finds answer between known markers
    2. Clean text extraction (fallback) - filters UI elements from full text
    3. Direct answer container (last resort) - tries various answer selectors

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
                # NOTE: .text_all is a PROPERTY, not an async method - do NOT await it
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
                    # NOTE: .text_all is a PROPERTY, not an async method - do NOT await it
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
                            # NOTE: .text_all is a PROPERTY, not an async method - do NOT await it
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
                    # NOTE: .text_all is a PROPERTY, not an async method - do NOT await it
                    text = el.text_all

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
