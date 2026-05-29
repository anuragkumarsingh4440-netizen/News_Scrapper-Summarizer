"""Rate-limiting strategies (Strategy pattern).

Different sources want different throttling behaviour. Rather than hard-code one
algorithm, fetchers accept a ``RateLimitStrategy`` and call ``acquire`` /
``release`` around each request. Swapping the algorithm is a one-line change at
the call site.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime


class RateLimitStrategy(ABC):
    """Abstract strategy for rate limiting."""

    @abstractmethod
    async def acquire(self) -> None:
        """Acquire permission to make a request (may block)."""
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        """Release permission after a request completes."""
        raise NotImplementedError


class SemaphoreStrategy(RateLimitStrategy):
    """Limit the number of *concurrent* in-flight requests."""

    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self) -> None:
        await self.semaphore.acquire()

    def release(self) -> None:
        self.semaphore.release()


class TokenBucketStrategy(RateLimitStrategy):
    """Token-bucket limiter: allows bursts but caps the average rate."""

    def __init__(self, rate: int, per: float) -> None:
        """Allow ``rate`` requests per ``per`` seconds."""
        self.rate = rate
        self.per = per
        self.allowance = float(rate)
        self.last_check = datetime.now()

    async def acquire(self) -> None:
        current = datetime.now()
        time_passed = (current - self.last_check).total_seconds()
        self.last_check = current

        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.rate:
            self.allowance = float(self.rate)

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0

    def release(self) -> None:  # noqa: D401 - nothing to release for a bucket
        """No-op: token buckets have no per-request resource to free."""
        return None
