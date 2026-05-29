"""Abstract base class for all article fetchers.

Demonstrates two principles at once:

* **Open/Closed** — new sources are added by subclassing, never by editing
  existing fetchers.
* **Template Method** — :meth:`fetch_and_save` defines the fixed
  fetch-then-save skeleton; subclasses only fill in the source-specific
  :meth:`fetch_articles` and :meth:`get_source_name`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class BaseFetcher(ABC):
    """Contract every fetcher must follow."""

    def __init__(
        self,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
    ) -> None:
        self.transformer = transformer
        self.storage = storage

    @abstractmethod
    async def fetch_articles(self) -> list[Article]:
        """Fetch and return articles from this source.

        Implementations must always return a list (empty on failure) so the
        fetcher stays Liskov-substitutable.
        """
        raise NotImplementedError

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the short source identifier, e.g. ``'hackernews'``."""
        raise NotImplementedError

    async def fetch_and_save(self) -> list[Article]:
        """Template method: fetch, then persist via the injected storage."""
        articles = await self.fetch_articles()
        if articles:
            self.storage.save(articles, f"{self.get_source_name()}_articles.md")
        return articles
