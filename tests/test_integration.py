"""Integration tests that touch the network or the MCP server.

These are skipped by default. Run them explicitly with::

    pytest -m integration
"""

import pytest

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer

pytestmark = pytest.mark.integration


async def test_hackernews_fetch_live(tmp_path):
    fetcher = HackerNewsFetcher(
        ArticleTransformer(), MarkdownStorage(str(tmp_path)), limit=5
    )
    articles = await fetcher.fetch_articles()
    assert len(articles) > 0
    assert all(a.source == "hackernews" for a in articles)


async def test_rss_fetch_live(tmp_path):
    fetcher = RSSFetcher(
        "https://hnrss.org/frontpage",
        ArticleTransformer(),
        MarkdownStorage(str(tmp_path)),
    )
    articles = await fetcher.fetch_articles()
    assert len(articles) > 0


async def test_database_mcp_server_roundtrip(tmp_path):
    """Spin up the database MCP server and call its tools end-to-end."""
    import sys

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "src.mcp_servers.database_server"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert {"query_articles", "search_articles", "get_sources"} <= names
