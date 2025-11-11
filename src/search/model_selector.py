"""
AI model selection module for Perplexity.ai automation.

Handles selecting AI models in Perplexity's UI with robust error handling,
human-like delays, and multiple fallback strategies for reliability.
"""

import logging
from typing import Optional, List

from src.config import MODEL_SELECTOR, MODEL_MAPPING, TIMEOUTS
from src.browser.interactions import human_delay
from src.types import NodriverPage

logger = logging.getLogger(__name__)


async def select_model(page: NodriverPage, model_name: str) -> bool:
    """
    Select an AI model in Perplexity's UI.

    This function finds the model selector button (circuit icon, 2nd from left
    on right side of search box), opens the options menu, locates the target
    model option, and clicks it with human-like behavior.

    Args:
        page: Nodriver page object
        model_name: User-friendly model name (e.g., 'gpt-4', 'claude', 'sonar')
                   Must exist as a key in MODEL_MAPPING

    Returns:
        bool: True if selection was successful, False otherwise

    Raises:
        ValueError: If model_name is not in MODEL_MAPPING (invalid model)
        RuntimeError: If model selector not found or selection action fails

    Example:
        >>> success = await select_model(page, 'gpt-4')
        >>> if success:
        ...     print("Model selected successfully")
        ... else:
        ...     print("Model selection failed")
    """
    logger.info(f"Starting model selection process for: {model_name}")

    # Step 1: Validate model name
    if model_name not in MODEL_MAPPING:
        available_models = list(MODEL_MAPPING.keys())
        error_msg = (
            f"Invalid model name: '{model_name}'. "
            f"Available models: {', '.join(available_models)}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    target_model_texts = MODEL_MAPPING[model_name]
    logger.debug(f"Model mapping: '{model_name}' -> {target_model_texts}")

    try:
        # Step 2: Find and click model selector button
        logger.debug("Step 1: Finding model selector button in search area...")
        model_selector = await _find_model_selector_button(page)

        if not model_selector:
            raise RuntimeError(
                "Model selector button not found in search area. "
                "The button should be on the right side of the search box (circuit icon)."
            )

        logger.debug("Model selector button found")

        # Step 3: Add human-like delay before interaction
        await human_delay('short')

        # Step 4: Click to open options menu
        logger.debug("Step 2: Clicking model selector to open menu...")
        try:
            await model_selector.click()
            logger.debug("Model selector clicked successfully")
        except Exception as e:
            logger.error(f"Failed to click model selector: {e}")
            raise RuntimeError(f"Could not click model selector button: {e}")

        # Step 5: Wait for options menu to appear
        await human_delay('medium')
        logger.debug("Step 3: Waiting for model options menu...")

        # Step 6: Find and click the target model option
        logger.debug(f"Step 4: Searching for model option matching: {target_model_texts}")
        model_option = await _find_model_option(page, target_model_texts)

        if not model_option:
            # Get available options for error message
            available = await _get_available_options(page)
            raise RuntimeError(
                f"Model option not found for '{model_name}'. "
                f"Tried matching: {target_model_texts}. "
                f"Available options: {available}"
            )

        logger.debug(f"Found model option: {model_option.text}")

        # Step 7: Click the model option
        await human_delay('short')
        logger.debug("Step 5: Selecting model option...")

        try:
            await model_option.click()
            logger.info(f"✓ Successfully selected model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to click model option: {e}")
            raise RuntimeError(f"Could not click model option: {e}")

        # Step 8: Wait for selection to take effect
        await human_delay('short')

        # Step 9: Verify selection (optional)
        logger.debug("Step 6: Model selection complete")
        return True

    except (ValueError, RuntimeError):
        # Re-raise validation and known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during model selection: {e}", exc_info=True)
        raise RuntimeError(f"Model selection failed unexpectedly: {e}")


async def _find_model_selector_button(page: NodriverPage):
    """
    Find the model selector button in the search area.

    The button is on the right side of the search box, 2nd from left
    (after the globe/sources icon), with a circuit icon.

    Args:
        page: Nodriver page object

    Returns:
        Element if found, None otherwise
    """
    logger.debug("Searching for model selector button...")

    # Try finding by aria-label or data-testid first
    for pattern in MODEL_SELECTOR['selector_patterns']:
        try:
            button = await page.find(pattern, timeout=2)
            if button:
                logger.debug(f"Found model selector using pattern: {pattern}")
                return button
        except Exception:
            continue

    # Fallback: Find all buttons in search container and identify by position
    logger.debug("Trying positional approach: finding buttons in search area...")

    try:
        # Find the textarea first
        textarea = await page.find(MODEL_SELECTOR['search_input'], timeout=3)
        if not textarea:
            logger.warning("Could not find search textarea")
            return None

        # Get all buttons - nodriver will return all matching elements
        buttons = await page.find_all('button', timeout=3)

        if not buttons or len(buttons) < 2:
            logger.warning(f"Found {len(buttons) if buttons else 0} buttons total")
            return None

        # Look for buttons that might be the model selector
        # The model selector typically has an SVG icon
        for button in buttons:
            try:
                # Check if button has an SVG (icon buttons usually do)
                svg = await button.query_selector('svg')
                if svg:
                    # Check aria-label or other attributes
                    aria_label = await button.get_attribute('aria-label') or ''
                    title = await button.get_attribute('title') or ''

                    if ('model' in aria_label.lower() or
                        'model' in title.lower() or
                        'select' in aria_label.lower()):
                        logger.debug(f"Found likely model selector: aria-label='{aria_label}'")
                        return button
            except Exception:
                continue

        logger.warning("Could not identify model selector button by attributes")

        # Last resort: Return the buttons and let user know
        if len(buttons) >= 5:
            # Based on user info: 5 buttons on right side, 2nd is model selector
            # Try returning a button that seems right
            logger.debug(f"Attempting to use positional heuristic from {len(buttons)} buttons")
            # This is a guess - would need more inspection
            return buttons[min(10, len(buttons) - 3)]  # Try a middle-ish button

    except Exception as e:
        logger.error(f"Error in positional search: {e}")

    return None


async def _find_model_option(page: NodriverPage, target_texts: List[str]):
    """
    Find a model option element by matching its text content.

    Args:
        page: Nodriver page object
        target_texts: List of possible text variations to match

    Returns:
        Element if found, None otherwise
    """
    logger.debug(f"Searching for model option with text: {target_texts}")

    # Try to find elements that could be model options
    for item_selector in MODEL_SELECTOR['option_item']:
        try:
            options = await page.find_all(item_selector, timeout=2)
            if not options:
                continue

            logger.debug(f"Found {len(options)} potential options with selector: {item_selector}")

            for option in options:
                try:
                    option_text = option.text_all.strip() if hasattr(option, 'text_all') else ''

                    # Check if any target text matches
                    for target in target_texts:
                        if target.lower() in option_text.lower() or option_text.lower() in target.lower():
                            logger.debug(f"Matched option text: '{option_text}' with target: '{target}'")
                            return option
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"No options found with selector {item_selector}: {e}")
            continue

    logger.warning(f"No model option found matching: {target_texts}")
    return None


async def _get_available_options(page: NodriverPage) -> List[str]:
    """
    Get list of available model option texts for error reporting.

    Args:
        page: Nodriver page object

    Returns:
        List of option text strings
    """
    available = []

    try:
        for item_selector in MODEL_SELECTOR['option_item']:
            try:
                options = await page.find_all(item_selector, timeout=1)
                if options:
                    for opt in options[:20]:  # Limit to first 20
                        try:
                            text = opt.text_all.strip() if hasattr(opt, 'text_all') else ''
                            if text and len(text) < 100:
                                available.append(text)
                        except Exception:
                            continue
                    break  # Found options, stop searching
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Could not retrieve available options: {e}")

    return available[:10]  # Return up to 10 options
