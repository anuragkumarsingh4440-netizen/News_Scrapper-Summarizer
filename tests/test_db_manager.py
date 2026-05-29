"""Tests for the async SQLite DatabaseManager."""

from datetime import datetime

from src.database.db_manager import DatabaseManager


def _article(url: str, source: str = "test") -> dict:
    return {
        "title": f"Article {url}",
        "url": url,
        "source": source,
        "published_at": datetime.now().isoformat(),
        "summary": "summary",
    }


async def test_insert_and_query(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(_article("https://a.com/1"))
    rows = await db.query_articles(limit=10)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://a.com/1"


async def test_duplicate_url_is_ignored(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(_article("https://a.com/dup"))
    await db.insert_article(_article("https://a.com/dup"))
    rows = await db.query_articles(limit=10)
    assert len(rows) == 1


async def test_query_filters_by_source(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(_article("https://a.com/1", source="hackernews"))
    await db.insert_article(_article("https://a.com/2", source="rss"))
    hn = await db.query_articles(source="hackernews", limit=10)
    assert len(hn) == 1
    assert hn[0]["source"] == "hackernews"
