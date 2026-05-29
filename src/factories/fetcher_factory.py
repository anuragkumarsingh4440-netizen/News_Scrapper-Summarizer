"""Factory for creating fetchers by name (Factory pattern).

Lets configuration / the orchestrator create fetchers from a string identifier
without importing every concrete class. New fetchers can be added to the
registry via :meth:`register` without modifying this class (OCP).
"""

from __future__ import annotations

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class FetcherFactory:
    """Creates fetcher instances from a registered type name."""

    _fetchers: dict[str, type[BaseFetcher]] = {
        "hackernews": HackerNewsFetcher,
        "rss": RSSFetcher,
        "github": GitHubTrendingFetcher,
    }

    @classmethod
    def create(
        cls,
        source_type: str,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
        **kwargs,
    ) -> BaseFetcher:
        """Create a fetcher by type name.

        Raises:
            ValueError: if ``source_type`` is unknown, or RSS is requested
                without a ``feed_url``.
        """
        if source_type not in cls._fetchers:
            raise ValueError(f"Unknown fetcher type: {source_type}")

        if source_type == "rss":
            feed_url = kwargs.get("feed_url")
            if not feed_url:
                raise ValueError("RSS fetcher requires feed_url")
            return RSSFetcher(feed_url, transformer, storage)

        return cls._fetchers[source_type](transformer, storage, **kwargs)

    @classmethod
    def register(cls, name: str, fetcher_class: type[BaseFetcher]) -> None:
        """Register a new fetcher type (extends the factory without editing it)."""
        cls._fetchers[name] = fetcher_class

    @classmethod
    def get_available_types(cls) -> list[str]:
        return list(cls._fetchers.keys())
