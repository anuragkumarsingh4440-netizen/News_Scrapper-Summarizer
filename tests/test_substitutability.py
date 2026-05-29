"""Liskov Substitution tests: every fetcher honors the BaseFetcher contract."""

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


def _all_fetchers(tmp_path):
    transformer = ArticleTransformer()
    storage = MarkdownStorage(str(tmp_path))
    return [
        HackerNewsFetcher(transformer, storage),
        RSSFetcher("https://hnrss.org/frontpage", transformer, storage),
        GitHubTrendingFetcher(transformer, storage),
    ]


def test_all_fetchers_share_interface(tmp_path):
    for fetcher in _all_fetchers(tmp_path):
        assert isinstance(fetcher, BaseFetcher)
        assert hasattr(fetcher, "fetch_articles")
        assert hasattr(fetcher, "fetch_and_save")
        assert isinstance(fetcher.get_source_name(), str)
        assert fetcher.get_source_name()


def test_fetchers_are_polymorphic(tmp_path):
    def source_of(fetcher: BaseFetcher) -> str:
        return fetcher.get_source_name()

    fetchers = _all_fetchers(tmp_path)
    names = {source_of(f) for f in fetchers}
    assert names == {"hackernews", "rss", "github_trending"}
