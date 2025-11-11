"""
Authentication and cookie management for Perplexity.ai
Handles session cookies, authentication verification, and cookie injection via CDP
"""
import logging
from typing import List, Dict
import nodriver as uc

from src.config import REQUIRED_COOKIES, COOKIE_DEFAULTS, SELECTORS, TIMEOUTS
from src.utils.decorators import async_retry
from src.browser.interactions import human_delay

logger = logging.getLogger(__name__)


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
