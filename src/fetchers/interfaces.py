"""Optional, focused fetcher interfaces (Interface Segregation Principle).

``BaseFetcher`` stays intentionally minimal — every fetcher needs those three
methods. Capabilities that only *some* sources need live here as separate
mix-in interfaces, so a simple fetcher is never forced to implement
``authenticate`` or ``fetch_page``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.article import Article


class AuthenticatedFetcher(ABC):
    """Mix-in for sources that require authentication before fetching."""

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the source; return True on success."""
        raise NotImplementedError


class PaginatedFetcher(ABC):
    """Mix-in for sources that expose paginated results."""

    @abstractmethod
    async def fetch_page(self, page: int) -> list[Article]:
        """Fetch a single page (1-indexed) of results."""
        raise NotImplementedError
