"""Tests for FetcherFactory (Factory pattern)."""

import pytest

from src.factories.fetcher_factory import FetcherFactory
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


@pytest.fixture
def deps(tmp_path):
    return ArticleTransformer(), MarkdownStorage(str(tmp_path))


def test_create_hackernews(deps):
    fetcher = FetcherFactory.create("hackernews", *deps)
    assert isinstance(fetcher, HackerNewsFetcher)
    assert fetcher.get_source_name() == "hackernews"


def test_create_github(deps):
    assert isinstance(FetcherFactory.create("github", *deps), GitHubTrendingFetcher)


def test_create_rss_requires_feed_url(deps):
    with pytest.raises(ValueError):
        FetcherFactory.create("rss", *deps)
    fetcher = FetcherFactory.create("rss", *deps, feed_url="http://feed")
    assert isinstance(fetcher, RSSFetcher)


def test_create_unknown_type_raises(deps):
    with pytest.raises(ValueError):
        FetcherFactory.create("nope", *deps)


def test_available_types_contains_registered():
    types = FetcherFactory.get_available_types()
    assert {"hackernews", "rss", "github"} <= set(types)
