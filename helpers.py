import asyncio
import random
import time
from functools import wraps
from typing import Callable, Any, Tuple, Type
from loguru import logger


def random_delay(min_seconds: int = 5, max_seconds: int = 30) -> None:
    """Introduces a random delay to prevent bot detection."""
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"Pausing for {delay:.2f} seconds...")
    time.sleep(delay)


async def async_random_delay(min_seconds: int = 5, max_seconds: int = 30) -> None:
    """Introduces an asynchronous random delay."""
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"Async pausing for {delay:.2f} seconds...")
    await asyncio.sleep(delay)


def retry(
    attempts: int = 3,
    delay: int = 5,
    catch_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff: float = 1.0,
    jitter: bool = True
) -> Callable[..., Callable[..., Any]]:
    """A decorator for retrying a function multiple times with exponential backoff.

    Args:
        attempts: The number of times to retry.
        delay: The initial delay in seconds between retries.
        catch_exceptions: A tuple of exceptions to catch and retry on.
        backoff: Exponential backoff multiplier (1.0 = no backoff, 2.0 = double delay each time).
        jitter: Whether to add random jitter to delays.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, attempts + 1):
                try:
                    logger.info(f"Attempt {attempt}/{attempts} for {func.__name__}")
                    return await func(*args, **kwargs)
                except catch_exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{attempts} failed for {func.__name__}: {str(e)[:100]}")

                    if attempt < attempts:
                        wait_time = current_delay
                        if jitter:
                            wait_time = wait_time * (0.5 + random.random())
                        logger.info(f"Retrying in {wait_time:.2f} seconds...")
                        await asyncio.sleep(wait_time)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {attempts} attempts failed for {func.__name__}.")

            raise last_exception or Exception(f"All {attempts} attempts failed for {func.__name__}")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, attempts + 1):
                try:
                    logger.info(f"Attempt {attempt}/{attempts} for {func.__name__}")
                    return func(*args, **kwargs)
                except catch_exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{attempts} failed for {func.__name__}: {str(e)[:100]}")

                    if attempt < attempts:
                        wait_time = current_delay
                        if jitter:
                            wait_time = wait_time * (0.5 + random.random())
                        logger.info(f"Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {attempts} attempts failed for {func.__name__}.")

            raise last_exception or Exception(f"All {attempts} attempts failed for {func.__name__}")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def handle_network_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for handling network-related errors specifically."""
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        network_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        try:
            return await func(*args, **kwargs)
        except network_errors as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        network_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        try:
            return func(*args, **kwargs)
        except network_errors as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
