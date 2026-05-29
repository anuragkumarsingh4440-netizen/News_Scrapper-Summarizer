"""Fetch trending repositories from GitHub.

This is the **Open/Closed Principle** proof: a complete third source added by
subclassing :class:`BaseFetcher` with ZERO edits to the existing fetchers,
transformer, or storage.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article


class GitHubTrendingFetcher(BaseFetcher):
    """Scrapes https://github.com/trending for trending repositories."""

    URL = "https://github.com/trending"

    def get_source_name(self) -> str:
        return "github_trending"

    async def fetch_articles(self) -> list[Article]:
        print("📰 Fetching trending repositories from GitHub...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.URL) as resp:
                    html = await resp.text()
        except Exception as exc:
            print(f"⚠️  GitHub Trending fetch failed: {exc}")
            return []

        articles = self._parse(html)
        print(f"✅ Fetched {len(articles)} trending repositories")
        return articles

    def _parse(self, html: str) -> list[Article]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[Article] = []

        for repo in soup.select("article.Box-row")[:20]:
            title_elem = repo.select_one("h2 a")
            if not title_elem:
                continue

            title = " ".join(title_elem.get_text().split())
            href = title_elem.get("href", "")
            url = f"https://github.com{href}"

            description_elem = repo.select_one("p")
            description = description_elem.get_text().strip() if description_elem else ""

            stars_elem = repo.select_one("a[href$='/stargazers']")
            stars = stars_elem.get_text().strip() if stars_elem else "0"

            articles.append(
                Article(
                    title=title,
                    url=url,
                    published_at=datetime.now(),
                    source="github_trending",
                    summary=f"{description} (⭐ {stars})",
                    score=0,
                )
            )

        return articles


if __name__ == "__main__":
    from src.storage.markdown_storage import MarkdownStorage
    from src.transformers.article_transformer import ArticleTransformer

    async def _demo() -> None:
        fetcher = GitHubTrendingFetcher(ArticleTransformer(), MarkdownStorage())
        articles = await fetcher.fetch_articles()
        for a in articles[:5]:
            print(f"  - {a.title}")

    asyncio.run(_demo())
