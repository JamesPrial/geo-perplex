"""
Result extraction module for Perplexity.ai search automation

This module handles extracting search results from the page using multiple
fallback strategies to ensure reliability even when UI structure changes.
"""
import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.config import (
    EXTRACTION_MARKERS,
    SELECTORS,
    TIMEOUTS,
    SCREENSHOT_CONFIG,
    STABILITY_CONFIG
)
from src.browser.interactions import human_delay
from src.browser.element_waiter import ElementWaiter
from src.types import NodriverPage

logger = logging.getLogger(__name__)


# Compile patterns once at module level for performance
_ERROR_PATTERNS = [
    re.compile(r'error|failed|sorry|couldn\'t|unable to|something went wrong', re.IGNORECASE),
    re.compile(r'no results|not found|try again', re.IGNORECASE)
]

# Maximum text size to check for patterns (prevent ReDoS)
_MAX_TEXT_CHECK_SIZE = 10000  # Only check first 10K characters


@dataclass
class ExtractionResult:
    """
    Result of a search extraction operation with full metadata.

    Attributes:
        success: Whether extraction was successful
        answer_text: Extracted answer text
        sources: List of source dictionaries with 'url' and 'text' keys
        strategy_used: Which extraction strategy succeeded (1, 2, or 3)
        extraction_time: Time spent extracting in seconds
        error: Error message if extraction failed
    """
    success: bool
    answer_text: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    strategy_used: Optional[str] = None
    extraction_time: float = 0.0
    error: Optional[str] = None


def _validate_extraction(
    answer_text: str,
    sources: Optional[List[Dict[str, str]]]
) -> tuple[bool, Optional[str]]:
    """
    Validate extracted search results.

    Checks for minimum content, error messages, and valid sources.
    Limits regex checks to first 10K characters to prevent ReDoS.

    Args:
        answer_text: Extracted answer text
        sources: Optional list of source dictionaries with 'url' and 'text' keys (None is acceptable)

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid, string describing issue if invalid
    """
    # Check minimum length
    if len(answer_text) < 20:
        return False, f"Answer too short ({len(answer_text)} chars)"

    # Limit text size for regex checks (prevent ReDoS on huge inputs)
    text_to_check = answer_text[:_MAX_TEXT_CHECK_SIZE]

    # Note if text was truncated for checking
    was_truncated = len(answer_text) > _MAX_TEXT_CHECK_SIZE
    truncation_note = f" (checked first {_MAX_TEXT_CHECK_SIZE} chars)" if was_truncated else ""

    # Check for error messages using pre-compiled patterns
    for pattern in _ERROR_PATTERNS:
        match = pattern.search(text_to_check)
        if match:
            return False, (
                f"Error message detected{truncation_note}: "
                f"'{match.group()}' matched pattern {pattern.pattern}"
            )

    # Validate sources structure (if sources exist)
    # Sources are optional - extraction is valid even without them
    if sources is not None and len(sources) > 0:
        # Check that sources have valid URLs
        valid_sources = 0
        for source in sources:
            if isinstance(source, dict) and source.get('url'):
                url = source['url']
                # Basic URL validation
                if url.startswith(('http://', 'https://')):
                    valid_sources += 1

        if valid_sources == 0:
            return False, f"No valid source URLs found (got {len(sources)} sources)"
    else:
        # No sources found but answer text is valid - this is acceptable
        logger.debug("No sources found, but answer text is valid - proceeding with extraction")

    # All checks passed
    return True, None


async def extract_search_results(page: NodriverPage, screenshot_path: Optional[str]) -> ExtractionResult:
    """
    Extract search results from the page with multiple fallback strategies.

    This function implements a 3-tier extraction strategy:
    1. Marker-based extraction (most accurate) - finds answer between known markers
    2. Clean text extraction (fallback) - filters UI elements from full text
    3. Direct answer container (last resort) - tries various answer selectors

    Args:
        page: Nodriver page object
        screenshot_path: Path to save screenshot (if enabled)

    Returns:
        ExtractionResult with success status, answer text, sources, and metadata
    """
    extraction_start = time.time()

    try:
        logger.info('Checking if search initiated...')

        # Create waiter instance for intelligent waiting
        waiter = ElementWaiter(page, poll_interval=0.1, verbose=False)

        # First, verify that the search actually started
        # Use wall clock time (time.time()) consistently for reliable timing under system load
        search_started = False
        start_time = time.time()

        while (time.time() - start_time) < TIMEOUTS['search_initiation']:
            # Check for URL change (most reliable indicator)
            if page.url and '/search' in page.url:
                search_started = True
                logger.info('Search initiated (detected URL change)')
                break

            # Check for loading indicators from config
            for selector in SELECTORS['loading_indicators']:
                result = await waiter.wait_for_presence(selector, timeout=1)
                if result.success:
                    search_started = True
                    logger.info(f'Search initiated (detected: {selector})')
                    break

            if search_started:
                break

            await asyncio.sleep(0.5)

        if not search_started:
            logger.warning('Could not confirm search started, proceeding anyway...')

        # Wait for "ask a follow-up" text to appear (indicates answer completion)
        logger.info('Waiting for answer completion...')
        followup_result = await waiter.wait_for_text(
            'main',
            'ask a follow-up',
            partial=True,
            timeout=TIMEOUTS['content_stability']
        )

        if followup_result.success:
            logger.info(f'Answer completed (detected follow-up prompt after {followup_result.wait_time:.2f}s)')
        else:
            # Fallback: Use stability detection
            logger.info('Follow-up prompt not detected, using content stability detection...')
            stability_result = await waiter.wait_for_stable(
                'main',
                timeout=TIMEOUTS['content_stability'],
                stable_threshold=STABILITY_CONFIG['stable_threshold'],
                min_content_length=STABILITY_CONFIG['min_content_length']
            )
            if not stability_result.success:
                logger.warning('Content stability timeout, proceeding with current content')

        # Additional short wait to ensure rendering complete
        await human_delay('short')

        logger.info('Extracting results...')

        # Take screenshot for debugging (if enabled)
        if screenshot_path:
            await page.save_screenshot(screenshot_path, full_page=SCREENSHOT_CONFIG['full_page'])
            logger.info(f'Screenshot saved: {screenshot_path}')

        # Extract the main answer/response using multiple strategies
        answer_text = ''
        strategy_used = None

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
                            strategy_used = 'Strategy 1: Marker-based'
                            logger.info(f'{strategy_used}: Found answer text ({len(answer_text)} chars)')

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
                            strategy_used = 'Strategy 2: Clean text'
                            logger.info(f'{strategy_used}: Found answer text ({len(answer_text)} chars)')
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
                                strategy_used = f'Strategy 3: Direct container ({selector})'
                                logger.info(f'{strategy_used}: Found answer text ({len(answer_text)} chars)')
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

        # Validate extraction
        if not answer_text:
            extraction_time = time.time() - extraction_start
            logger.error('No answer text extracted from any strategy')
            return ExtractionResult(
                success=False,
                answer_text='No answer text extracted',
                sources=[],
                strategy_used=None,
                extraction_time=extraction_time,
                error='All extraction strategies failed'
            )

        # Validate content quality
        is_valid, validation_error = _validate_extraction(answer_text, sources)
        extraction_time = time.time() - extraction_start

        if not is_valid:
            logger.warning(f'Extraction validation failed: {validation_error}')
            return ExtractionResult(
                success=False,
                answer_text=answer_text,
                sources=sources,
                strategy_used=strategy_used,
                extraction_time=extraction_time,
                error=validation_error
            )

        # Success!
        logger.info(f'Extraction successful using {strategy_used} ({extraction_time:.2f}s)')
        return ExtractionResult(
            success=True,
            answer_text=answer_text,
            sources=sources,
            strategy_used=strategy_used,
            extraction_time=extraction_time,
            error=None
        )

    except Exception as error:
        extraction_time = time.time() - extraction_start
        logger.error(f'Could not extract complete results: {error}')
        return ExtractionResult(
            success=False,
            answer_text='Failed to extract results - page structure may have changed',
            sources=[],
            strategy_used=None,
            extraction_time=extraction_time,
            error=str(error)
        )
