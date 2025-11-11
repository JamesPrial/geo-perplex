"""
Reusable decorators for the application
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Any, Optional, List, TypeVar, ParamSpec, Awaitable, Union, overload, Literal
from src.config import RETRY_CONFIG

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


@dataclass
class RetryResult:
    """
    Result object from retry decorator with detailed execution information

    Attributes:
        success: Whether the function succeeded
        result: The return value from the function (None if failed)
        attempts: Number of attempts made
        errors: List of exceptions encountered
        total_time: Total execution time in seconds
    """
    success: bool
    result: Optional[Any] = None
    attempts: int = 0
    errors: List[Exception] = None
    total_time: float = 0.0

    def __post_init__(self) -> None:
        """Initialize errors list if None"""
        if self.errors is None:
            self.errors = []

    def __repr__(self) -> str:
        """String representation for debugging"""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"RetryResult({status}, attempts={self.attempts}, "
            f"time={self.total_time:.2f}s, errors={len(self.errors)})"
        )


@overload
def async_retry(
    max_attempts: Optional[int] = None,
    exceptions: tuple = (Exception,),
    return_result_object: Literal[False] = False
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...


@overload
def async_retry(
    max_attempts: Optional[int] = None,
    exceptions: tuple = (Exception,),
    return_result_object: Literal[True] = True
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[RetryResult]]]: ...


def async_retry(
    max_attempts: Optional[int] = None,
    exceptions: tuple = (Exception,),
    return_result_object: bool = False
) -> Union[
    Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]],
    Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[RetryResult]]]
]:
    """
    Decorator for retrying async functions with exponential backoff.

    This decorator preserves function signatures and provides proper type hints
    using ParamSpec and overloads for accurate type checking.

    Args:
        max_attempts: Maximum retry attempts (defaults to RETRY_CONFIG)
        exceptions: Tuple of exceptions to catch
        return_result_object: If True, returns RetryResult instead of raising on failure
                              (default False for backward compatibility)

    Returns:
        If return_result_object=False: Returns the function result or raises last exception
        If return_result_object=True: Returns RetryResult object with execution details

    Example:
        # Basic usage (backward compatible) - preserves original return type
        @async_retry(max_attempts=3)
        async def my_func() -> str:
            ...

        # With detailed result object - returns RetryResult
        @async_retry(max_attempts=3, return_result_object=True)
        async def my_func() -> str:
            ...

        result = await my_func()
        if result.success:
            print(f"Success after {result.attempts} attempts: {result.result}")
        else:
            print(f"Failed after {result.attempts} attempts: {result.errors}")

    Note:
        Type checkers will correctly infer return types based on return_result_object flag.
    """
    if max_attempts is None:
        max_attempts = RETRY_CONFIG['max_attempts']

    def decorator(func: Callable[P, Awaitable[T]]) -> Union[Callable[P, Awaitable[T]], Callable[P, Awaitable[RetryResult]]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, RetryResult]:
            last_exception = None
            errors: List[Exception] = []
            start_time = time.time()

            for attempt in range(max_attempts):
                attempt_start = time.time()
                try:
                    result = await func(*args, **kwargs)

                    # Success!
                    total_time = time.time() - start_time
                    logger.info(
                        f"{func.__name__} succeeded on attempt {attempt + 1}/{max_attempts} "
                        f"({total_time:.2f}s total)"
                    )

                    if return_result_object:
                        return RetryResult(
                            success=True,
                            result=result,
                            attempts=attempt + 1,
                            errors=errors,
                            total_time=total_time
                        )
                    else:
                        return result

                except exceptions as e:
                    last_exception = e
                    errors.append(e)
                    attempt_time = time.time() - attempt_start

                    if attempt < max_attempts - 1:
                        delay = RETRY_CONFIG['base_delay']
                        if RETRY_CONFIG['exponential']:
                            delay *= (RETRY_CONFIG['backoff_factor'] ** attempt)

                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}) "
                            f"after {attempt_time:.2f}s: {e}. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        total_time = time.time() - start_time
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts "
                            f"({total_time:.2f}s total): {e}"
                        )

            # All attempts failed
            total_time = time.time() - start_time

            if return_result_object:
                return RetryResult(
                    success=False,
                    result=None,
                    attempts=max_attempts,
                    errors=errors,
                    total_time=total_time
                )
            else:
                raise last_exception

        return wrapper
    return decorator