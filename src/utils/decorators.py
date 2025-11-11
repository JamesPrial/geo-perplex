"""
Reusable decorators for the application
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from src.config import RETRY_CONFIG

logger = logging.getLogger(__name__)


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