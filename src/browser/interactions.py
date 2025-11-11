"""
Browser interaction utilities for human-like behavior and element handling
"""
import asyncio
import random
import logging
from typing import List, Dict, Any, Optional
from src.config import HUMAN_BEHAVIOR, TIMEOUTS
from src.types import NodriverPage

logger = logging.getLogger(__name__)


async def human_delay(delay_type: str = 'short', distribution: str = 'exponential') -> None:
    """
    Add human-like random delays using natural distributions to avoid detection

    Args:
        delay_type: 'short', 'medium', or 'long'
        distribution: 'exponential' (default) or 'gaussian'

    Notes:
        - Exponential: Many short pauses, few long ones (mimics reaction time)
        - Gaussian: Delays cluster around mean with occasional outliers
    """
    delays = HUMAN_BEHAVIOR['delays']

    # Get min/max/variance for the delay type from config
    if delay_type == 'short':
        min_delay = delays['short_min']
        max_delay = delays['short_max']
        variance = delays['short_variance']
    elif delay_type == 'medium':
        min_delay = delays['medium_min']
        max_delay = delays['medium_max']
        variance = delays['medium_variance']
    elif delay_type == 'long':
        min_delay = delays['long_min']
        max_delay = delays['long_max']
        variance = delays['long_variance']
    else:
        # Default to medium
        min_delay = delays['medium_min']
        max_delay = delays['medium_max']
        variance = delays['medium_variance']

    base = (min_delay + max_delay) / 2

    # Generate delay using natural distribution
    if distribution == 'exponential':
        # Exponential distribution creates realistic pause patterns
        delay = random.expovariate(1 / base) * variance
        delay = max(min_delay, min(delay, max_delay))
    elif distribution == 'gaussian':
        # Gaussian distribution with delays clustering around mean
        mean = (min_delay + max_delay) / 2
        std_dev = (max_delay - min_delay) / 6  # ~99.7% within range
        delay = random.gauss(mean, std_dev)
        delay = max(min_delay, min(delay, max_delay))
    else:
        # Fallback to exponential
        delay = random.expovariate(1 / base) * variance
        delay = max(min_delay, min(delay, max_delay))

    await asyncio.sleep(delay)


async def _get_element_value(element) -> str:
    """
    Safely get element value or text content.

    Args:
        element: Nodriver element

    Returns:
        Element value or text content as string
    """
    try:
        # Try value attribute first (for input/textarea)
        value = element.get_attribute('value')
        # Check if it's awaitable (depends on nodriver version)
        if hasattr(value, '__await__'):
            value = await value
        if value is not None:
            return str(value)
    except (AttributeError, TypeError):
        pass

    # Fallback to text content
    try:
        if hasattr(element, 'text_all'):
            return element.text_all or ""
        elif hasattr(element, 'text'):
            return element.text or ""
    except (AttributeError, TypeError):
        pass

    return ""


async def _clear_element(element) -> bool:
    """
    Safely clear element input.

    Args:
        element: Nodriver element

    Returns:
        True if cleared successfully, False otherwise
    """
    try:
        # Try clear_input() method
        if hasattr(element, 'clear_input'):
            clear_op = element.clear_input()
            if hasattr(clear_op, '__await__'):
                await clear_op
            return True
    except Exception as e:
        logger.debug(f"clear_input() failed: {e}")

    try:
        # Fallback: select all and delete
        await element.send_keys('\x01')  # Ctrl+A
        await asyncio.sleep(0.05)
        await element.send_keys('\x08')  # Backspace
        return True
    except Exception as e:
        logger.debug(f"Keyboard clear failed: {e}")
        return False


async def type_like_human(
    element,
    text: str,
    verify: bool = True,
    max_retries: int = 2
) -> bool:
    """
    Type text character-by-character with human-like delays and verification.

    Args:
        element: Nodriver element to type into
        text: Text to type
        verify: Whether to verify text was entered correctly
        max_retries: Maximum retry attempts on verification failure

    Returns:
        True if typing succeeded (and verified if requested), False otherwise

    Raises:
        asyncio.TimeoutError: If typing operations timeout
        ConnectionError: If browser connection is lost
    """
    typing_speed = HUMAN_BEHAVIOR['typing_speed']

    for attempt in range(max_retries + 1):
        try:
            # Type character-by-character with human-like delays
            for i, char in enumerate(text):
                await element.send_keys(char)

                # Variable delays based on character type
                if char == ' ':
                    # Slightly longer pause at spaces (natural typing)
                    base = (typing_speed['space_min'] + typing_speed['space_max']) / 2
                    delay = random.expovariate(1 / base) * 0.4
                    delay = max(typing_speed['space_min'], min(delay, typing_speed['space_max']))
                else:
                    base = (typing_speed['char_min'] + typing_speed['char_max']) / 2
                    delay = random.expovariate(1 / base) * 0.3
                    delay = max(typing_speed['char_min'], min(delay, typing_speed['char_max']))

                await asyncio.sleep(delay)

                # Occasional micro-pause (simulates thinking/hesitation)
                if i > 0 and i % random.randint(8, 15) == 0:
                    await human_delay('short', 'exponential')

            # Verify text was entered correctly if requested
            if verify:
                await asyncio.sleep(0.1)  # Brief pause before verification
                entered_text = await _get_element_value(element)

                if entered_text == text:
                    logger.debug(f"Typing verified successfully on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(
                        f"Typing verification failed on attempt {attempt + 1}: "
                        f"expected '{text[:50]}...', got '{entered_text[:50]}...'"
                    )

                    # Retry if we have attempts left
                    if attempt < max_retries:
                        logger.debug("Clearing and retrying...")
                        await _clear_element(element)
                        await human_delay('short')
                        continue
                    else:
                        logger.error(
                            f"Typing verification failed after {max_retries + 1} attempts"
                        )
                        return False
            else:
                # No verification requested, assume success
                return True

        except (asyncio.TimeoutError, ConnectionError) as e:
            # Critical errors that should propagate or fail
            if attempt < max_retries:
                logger.warning(
                    f"Typing attempt {attempt + 1} failed with {type(e).__name__}: {e}"
                )
                await human_delay('short')
            else:
                logger.error(
                    f"All typing attempts failed with {type(e).__name__}: {e}"
                )
                return False
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error during typing: {type(e).__name__}: {e}")
            if attempt >= max_retries:
                return False
            await human_delay('short')

    return False


async def find_interactive_element(page: NodriverPage, selectors: List[str], timeout: int = None):
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


async def health_check(page: NodriverPage) -> Dict[str, Any]:
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


async def scroll_naturally(
    page,
    total_pixels: Optional[int] = None,
    smoothness: float = 0.8,
    reading_speed: float = 1.0
) -> None:
    """
    Scroll through a page with natural human-like patterns

    Args:
        page: Nodriver page object
        total_pixels: Total pixels to scroll (None = scroll to bottom)
        smoothness: How smooth scrolling is (0.1 to 1.0, higher = smoother)
        reading_speed: Reading speed multiplier (0.5 to 2.0)

    Notes:
        - Variable speed scrolling (fast at start, slow at end)
        - Random pauses during scroll (simulate reading)
        - Uses exponential distribution for natural timing
    """
    try:
        # Get page dimensions
        viewport_height = await page.evaluate('window.innerHeight')
        scroll_height = await page.evaluate('document.body.scrollHeight')
        current_scroll = await page.evaluate('window.pageYOffset')

        if scroll_height <= viewport_height:
            logger.debug('Page does not need scrolling')
            return

        # Calculate total scroll distance
        if total_pixels is None:
            total_pixels = scroll_height - viewport_height - current_scroll

        if total_pixels <= 0:
            return

        # Generate scroll increments with variance
        num_increments = max(5, int(total_pixels / (50 * smoothness)))
        base_increment = total_pixels / num_increments

        scrolled = 0
        for i in range(num_increments):
            # Variable scroll speed with Gaussian variance
            variance = random.gauss(1.0, 0.3)  # 30% variance
            increment = max(10, base_increment * variance)

            # Don't overshoot
            if scrolled + increment > total_pixels:
                increment = total_pixels - scrolled

            # Perform scroll
            await page.evaluate(f'window.scrollBy(0, {increment})')
            scrolled += increment

            logger.debug(f'Scrolled {increment:.0f}px (total: {scrolled:.0f}/{total_pixels:.0f}px)')

            # Pause for reading with exponential distribution
            # Longer pauses for more content
            # Safety bounds prevent division by zero
            estimated_words = max(1, (increment / 240) * 250)  # At least 1 word
            base_reading_time = max(0.1, (estimated_words / 200) * 60)  # Minimum 0.1s
            dwell_time = base_reading_time * reading_speed

            # Add natural variance to dwell time with safe bounds
            try:
                dwell_with_variance = random.expovariate(1 / dwell_time) * 0.5
            except (ValueError, ZeroDivisionError):
                # Fallback if calculation fails
                dwell_with_variance = dwell_time * 0.5

            # Clamp final value to reasonable range
            dwell_with_variance = max(0.1, min(dwell_with_variance, 3.0))

            await asyncio.sleep(dwell_with_variance)

            # Occasionally add longer pause (simulate careful reading)
            if random.random() < 0.2:  # 20% chance
                pause_duration = random.uniform(0.5, 2.0) * reading_speed
                logger.debug(f'Reading pause: {pause_duration:.1f}s')
                await asyncio.sleep(pause_duration)

            if scrolled >= total_pixels:
                break

        logger.info(f'Natural scrolling complete: scrolled {scrolled:.0f}px')

    except Exception as e:
        logger.warning(f'Error during natural scrolling: {e}')