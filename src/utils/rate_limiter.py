"""Simple semaphore-based rate limiter.

Used to cap how many concurrent HTTP requests a fetcher makes against a single
host so we stay polite to public APIs.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


class RateLimiter:
    """Limits the number of concurrent operations via an asyncio Semaphore."""

    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self) -> RateLimiter:
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.semaphore.release()

    async def execute(self, coro: Awaitable[T]) -> T:
        """Run a coroutine while holding the semaphore."""
        async with self:
            return await coro


if __name__ == "__main__":
    import time

    async def _demo() -> None:
        limiter = RateLimiter(max_concurrent=2)

        async def slow_task(n: int) -> int:
            async with limiter:
                await asyncio.sleep(0.5)
                return n

        start = time.time()
        await asyncio.gather(*[slow_task(i) for i in range(4)])
        print(f"✅ Completed in {time.time() - start:.2f}s (expected ~1.0s)")

    asyncio.run(_demo())
