import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

T = TypeVar("T")


def retryable(exc: Exception) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
        408,
        429,
        *range(500, 600),
    }


async def with_retry(operation: Callable[[], Awaitable[T]], retries: int) -> T:
    attempt = 0
    while True:
        try:
            return await operation()
        except Exception as exc:
            if attempt >= retries or not retryable(exc):
                raise
            await asyncio.sleep(min(2**attempt, 8))
            attempt += 1
