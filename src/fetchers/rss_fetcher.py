"""Fetch articles from an RSS feed.

``feedparser`` is synchronous, so we run it in the default executor to keep the
event loop free.
"""

from __future__ import annotations

import asyncio

import feedparser

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class RSSFetcher(BaseFetcher):
    """Fetches and parses a single RSS feed."""

    def __init__(
        self,
        feed_url: str,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
    ) -> None:
        super().__init__(transformer, storage)
        self.feed_url = feed_url

    def get_source_name(self) -> str:
        return "rss"

    async def fetch_articles(self) -> list[Article]:
        print(f"📰 Fetching from RSS: {self.feed_url}")
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)
        except Exception as exc:
            print(f"⚠️  RSS fetch failed: {exc}")
            return []

        articles = self.transformer.transform_rss(feed.entries)
        print(f"✅ Fetched {len(articles)} RSS articles")
        return articles


if __name__ == "__main__":
    from src.storage.markdown_storage import MarkdownStorage

    async def _demo() -> None:
        fetcher = RSSFetcher(
            "https://hnrss.org/frontpage", ArticleTransformer(), MarkdownStorage()
        )
        articles = await fetcher.fetch_articles()
        for a in articles[:3]:
            print(f"  - {a.title[:60]}")

    asyncio.run(_demo())
