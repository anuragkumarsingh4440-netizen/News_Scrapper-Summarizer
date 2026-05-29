"""Tests for MarkdownStorage."""

import tempfile
from datetime import datetime

from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage


def _article(title: str) -> Article:
    return Article(
        title=title,
        url=f"https://example.com/{title}",
        published_at=datetime.now(),
        source="test",
        summary="summary",
    )


def test_save_creates_file_with_content():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MarkdownStorage(tmp)
        path = storage.save([_article("Hello")], "out.md")
        assert path.exists()
        assert "Hello" in path.read_text(encoding="utf-8")


def test_save_multiple_articles():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MarkdownStorage(tmp)
        path = storage.save([_article(f"A{i}") for i in range(5)])
        content = path.read_text(encoding="utf-8")
        assert "A0" in content and "A4" in content


def test_save_autogenerates_filename():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MarkdownStorage(tmp)
        path = storage.save([_article("X")])
        assert path.name.startswith("articles_")
