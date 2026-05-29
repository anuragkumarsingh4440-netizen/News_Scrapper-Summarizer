"""Fetch top stories from the HackerNews API.

API docs: https://github.com/HackerNews/API

Source-specific logic only — transformation is delegated to the injected
``ArticleTransformer`` and persistence to the injected storage.
"""

from __future__ import annotations

import asyncio

import aiohttp

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.strategies.rate_limit_strategy import RateLimitStrategy, SemaphoreStrategy
from src.transformers.article_transformer import ArticleTransformer


class HackerNewsFetcher(BaseFetcher):
    """Fetches top stories from HackerNews concurrently."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(
        self,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
        limit: int = 30,
        rate_limiter: RateLimitStrategy | None = None,
    ) -> None:
        super().__init__(transformer, storage)
        self.limit = limit
        self.rate_limiter = rate_limiter or SemaphoreStrategy(max_concurrent=10)

    def get_source_name(self) -> str:
        return "hackernews"

    async def fetch_articles(self) -> list[Article]:
        """Fetch top-story IDs, then fetch each story concurrently."""
        print(f"📰 Fetching {self.limit} stories from HackerNews...")
        try:
            async with aiohttp.ClientSession() as session:
                story_ids = await self._fetch_top_story_ids(session)
                tasks = [
                    self._fetch_story(session, sid) for sid in story_ids[: self.limit]
                ]
                raw_items = await asyncio.gather(*tasks)
        except Exception as exc:  # network failure → empty list, stays substitutable
            print(f"⚠️  HackerNews fetch failed: {exc}")
            return []

        articles = self.transformer.transform_hackernews(
            [item for item in raw_items if item]
        )
        print(f"✅ Fetched {len(articles)} HackerNews stories")
        return articles

    async def _fetch_top_story_ids(self, session: aiohttp.ClientSession) -> list[int]:
        async with session.get(f"{self.BASE_URL}/topstories.json") as resp:
            return await resp.json()

    async def _fetch_story(
        self, session: aiohttp.ClientSession, story_id: int
    ) -> dict | None:
        """Fetch a single story, throttled by the rate-limit strategy."""
        url = f"{self.BASE_URL}/item/{story_id}.json"
        await self.rate_limiter.acquire()
        try:
            async with session.get(url) as resp:
                return await resp.json()
        except Exception as exc:
            print(f"⚠️  Failed to fetch story {story_id}: {exc}")
            return None
        finally:
            self.rate_limiter.release()


if __name__ == "__main__":
    from src.storage.markdown_storage import MarkdownStorage

    async def _demo() -> None:
        fetcher = HackerNewsFetcher(ArticleTransformer(), MarkdownStorage(), limit=5)
        articles = await fetcher.fetch_articles()
        for a in articles:
            print(f"  - {a.title[:60]}")

    asyncio.run(_demo())
