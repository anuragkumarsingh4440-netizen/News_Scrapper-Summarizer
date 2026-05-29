"""Transform raw source data into Article objects.

Single Responsibility (SRP): this class only knows how to map the various raw
shapes returned by news sources onto the shared :class:`Article` model. Fetchers
stay focused on I/O; this stays focused on data mapping.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from dateutil import parser as date_parser

from src.models.article import Article


class ArticleTransformer:
    """Transforms raw data from various sources into Article objects."""

    def transform_hackernews(self, raw_data: list[dict]) -> list[Article]:
        """Transform a list of HackerNews API items into Articles.

        Items without a URL (Ask HN, job posts, etc.) are skipped.
        """
        articles: list[Article] = []

        for item in raw_data:
            if not item or not item.get("url"):
                continue

            text = item.get("text") or ""
            articles.append(
                Article(
                    title=item.get("title", "No Title"),
                    url=item["url"],
                    published_at=datetime.fromtimestamp(item.get("time", 0)),
                    source="hackernews",
                    summary=text[:200],
                    score=item.get("score", 0),
                )
            )

        return articles

    def transform_rss(self, entries: list[Any]) -> list[Article]:
        """Transform feedparser RSS entries into Articles."""
        articles: list[Article] = []

        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue

            summary = entry.get("summary", entry.get("description", "")) or ""
            summary = re.sub("<.*?>", "", summary)[:200]

            articles.append(
                Article(
                    title=entry.get("title", "No Title"),
                    url=url,
                    published_at=self._parse_date(
                        entry.get("published", entry.get("updated", ""))
                    ),
                    source="rss",
                    summary=summary,
                )
            )

        return articles

    def _parse_date(self, date_str: str | None) -> datetime:
        """Parse a date string, falling back to now() on failure."""
        if not date_str:
            return datetime.now()
        try:
            return date_parser.parse(date_str)
        except (ValueError, OverflowError, TypeError):
            return datetime.now()


if __name__ == "__main__":
    transformer = ArticleTransformer()
    raw = [{"title": "Test", "url": "http://example.com", "time": 1234567890}]
    out = transformer.transform_hackernews(raw)
    assert len(out) == 1 and out[0].title == "Test"
    print("✅ Transformer works!")
