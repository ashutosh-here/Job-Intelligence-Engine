from collections.abc import Callable
from functools import wraps
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def with_retry(
    attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 8,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        wrapped = retry(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True,
        )(func)

        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            return wrapped(*args, **kwargs)

        return inner

    return decorator
