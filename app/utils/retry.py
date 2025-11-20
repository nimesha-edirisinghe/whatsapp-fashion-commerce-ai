"""Async retry decorator with timeout."""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

from app.core.logging import logger

T = TypeVar("T")


def async_retry(
    attempts: int = 1,
    timeout: float = 3.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for async functions with retry and timeout.

    Args:
        attempts: Number of retry attempts (default 1 = total 2 tries)
        timeout: Timeout in seconds for each attempt
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(attempts + 1):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} timed out (attempt {attempt + 1}/{attempts + 1})"
                    )
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{attempts + 1}): {e}"
                    )

                if attempt < attempts:
                    # Brief delay before retry
                    await asyncio.sleep(0.1)

            # All attempts failed
            logger.error(f"{func.__name__} failed after {attempts + 1} attempts")
            raise last_exception or Exception(f"{func.__name__} failed")

        return wrapper
    return decorator
