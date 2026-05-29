"""Coordinates fetching from multiple sources concurrently.

Follows the Dependency Inversion Principle: it depends on the ``BaseFetcher``
and ``ArticleStorage`` abstractions and receives them via the constructor, so
it can be driven entirely by mocks in tests.
"""

from __future__ import annotations

import asyncio

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


class FetchOrchestrator:
    """Runs every configured fetcher concurrently and aggregates the results."""

    def __init__(
        self,
        fetchers: list[BaseFetcher],
        storage: ArticleStorage,
    ) -> None:
        self.fetchers = fetchers
        self.storage = storage

    @classmethod
    def with_defaults(
        cls,
        storage: ArticleStorage | None = None,
        transformer: ArticleTransformer | None = None,
        rss_feed: str = "https://hnrss.org/frontpage",
    ) -> FetchOrchestrator:
        """Build an orchestrator wired with the standard set of fetchers.

        Convenience constructor for the CLI / pipelines. Tests use the plain
        constructor with injected (mock) fetchers instead.
        """
        from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
        from src.fetchers.hackernews_fetcher import HackerNewsFetcher
        from src.fetchers.rss_fetcher import RSSFetcher

        transformer = transformer or ArticleTransformer()
        storage = storage or MarkdownStorage()
        fetchers: list[BaseFetcher] = [
            HackerNewsFetcher(transformer, storage),
            RSSFetcher(rss_feed, transformer, storage),
            GitHubTrendingFetcher(transformer, storage),
        ]
        return cls(fetchers, storage)

    async def fetch_all(self, save_combined: bool = True) -> list[Article]:
        """Fetch from all sources concurrently and return combined articles."""
        print(f"\n🚀 Fetching from {len(self.fetchers)} sources...")

        results = await asyncio.gather(
            *(fetcher.fetch_articles() for fetcher in self.fetchers),
            return_exceptions=True,
        )

        all_articles: list[Article] = []
        for fetcher, result in zip(self.fetchers, results, strict=False):
            name = fetcher.get_source_name()
            if isinstance(result, Exception):
                print(f"⚠️  {name} failed: {result}")
            else:
                print(f"✅ {name}: {len(result)} articles")
                all_articles.extend(result)

        if save_combined and all_articles:
            self.storage.save(all_articles, "all_articles.md")

        print(f"\n🎉 Total: {len(all_articles)} articles")
        return all_articles
