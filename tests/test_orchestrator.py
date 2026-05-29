"""Tests for FetchOrchestrator using mocks (Dependency Inversion in action)."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

from src.models.article import Article
from src.orchestration.orchestrator import FetchOrchestrator


def _mock_fetcher(name: str, articles: list[Article]):
    fetcher = Mock()
    fetcher.get_source_name = Mock(return_value=name)
    fetcher.fetch_articles = AsyncMock(return_value=articles)
    return fetcher


def _article(title: str) -> Article:
    return Article(title, f"http://{title}.com", datetime.now(), "test", "s")


async def test_fetch_all_combines_results():
    f1 = _mock_fetcher("a", [_article("one")])
    f2 = _mock_fetcher("b", [_article("two"), _article("three")])
    storage = Mock()

    orchestrator = FetchOrchestrator([f1, f2], storage)
    articles = await orchestrator.fetch_all()

    assert len(articles) == 3
    f1.fetch_articles.assert_awaited_once()
    storage.save.assert_called_once()


async def test_fetch_all_survives_a_failing_fetcher():
    good = _mock_fetcher("good", [_article("ok")])
    bad = Mock()
    bad.get_source_name = Mock(return_value="bad")
    bad.fetch_articles = AsyncMock(side_effect=RuntimeError("boom"))

    orchestrator = FetchOrchestrator([good, bad], Mock())
    articles = await orchestrator.fetch_all()

    # The good fetcher's articles still come through.
    assert len(articles) == 1


async def test_fetch_all_skips_save_when_empty():
    empty = _mock_fetcher("empty", [])
    storage = Mock()
    orchestrator = FetchOrchestrator([empty], storage)
    articles = await orchestrator.fetch_all()
    assert articles == []
    storage.save.assert_not_called()
