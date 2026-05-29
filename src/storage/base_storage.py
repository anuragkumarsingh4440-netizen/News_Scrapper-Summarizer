"""Storage interface (Dependency Inversion Principle).

Fetchers and the orchestrator depend on this abstraction, not on a concrete
storage class. That lets us swap in JSON / database / cloud storage later
without touching any of the calling code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.article import Article


class ArticleStorage(ABC):
    """Abstract interface for persisting articles."""

    @abstractmethod
    def save(self, articles: list[Article], filename: str | None = None) -> Path:
        """Persist a list of articles and return where they were saved."""
        raise NotImplementedError
