"""Tests for the Article model."""

from datetime import datetime

import pytest

from src.models.article import Article


def test_article_creation(sample_article_kwargs):
    article = Article(**sample_article_kwargs)
    assert article.title == sample_article_kwargs["title"]
    assert article.url == sample_article_kwargs["url"]
    assert article.score == 0
    assert article.summary == ""


def test_article_requires_title():
    with pytest.raises(ValueError):
        Article(title="", url="https://x.com", published_at=datetime.now(), source="t")


def test_article_requires_url():
    with pytest.raises(ValueError):
        Article(title="t", url="", published_at=datetime.now(), source="t")


def test_article_to_markdown(sample_article_kwargs):
    article = Article(**sample_article_kwargs, summary="A summary")
    md = article.to_markdown()
    assert "Sample article for tests" in md
    assert "https://example.com/sample" in md
    assert "A summary" in md
