import asyncio
import functools
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")
LOGGER = logging.getLogger("engine.retry")

def resilient_call(
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for retrying async functions with jittered backoff.
    
    Args:
        retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay capped.
        exponential: Whether to use exponential backoff.
        exceptions: Tuple of exceptions to catch and retry.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            while attempt <= retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt > retries:
                        LOGGER.error(
                            f"Final attempt failed for {func.__name__}: {e}", 
                            exc_info=True
                        )
                        raise e
                    
                    # Calculate delay with jitter
                    delay = base_delay * (2 ** (attempt - 1)) if exponential else base_delay
                    delay = min(delay, max_delay)
                    jitter = delay * 0.1 * random.uniform(-1, 1)
                    final_delay = max(0, delay + jitter)
                    
                    LOGGER.warning(
                        f"Attempt {attempt}/{retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {final_delay:.2f}s..."
                    )
                    await asyncio.sleep(final_delay)
            return None # Should not be reached
        return wrapper
    return decorator
