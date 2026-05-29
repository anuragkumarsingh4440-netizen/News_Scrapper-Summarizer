"""Tests for rate-limiting strategies and the RateLimiter util."""

import asyncio
import time

from src.strategies.rate_limit_strategy import SemaphoreStrategy, TokenBucketStrategy
from src.utils.rate_limiter import RateLimiter


async def test_semaphore_strategy_limits_concurrency():
    strategy = SemaphoreStrategy(max_concurrent=2)

    async def task():
        await strategy.acquire()
        try:
            await asyncio.sleep(0.1)
        finally:
            strategy.release()

    start = time.perf_counter()
    await asyncio.gather(*[task() for _ in range(4)])
    elapsed = time.perf_counter() - start
    # 4 tasks, 2 at a time, 0.1s each -> ~0.2s
    assert elapsed >= 0.18


async def test_token_bucket_allows_initial_burst():
    bucket = TokenBucketStrategy(rate=5, per=1.0)
    start = time.perf_counter()
    for _ in range(5):
        await bucket.acquire()
    # First `rate` acquisitions should be near-instant.
    assert time.perf_counter() - start < 0.1


async def test_rate_limiter_context_manager():
    limiter = RateLimiter(max_concurrent=1)
    async with limiter:
        pass  # acquire/release should not raise
