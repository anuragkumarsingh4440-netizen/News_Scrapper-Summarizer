"""Service layer that wraps the pipeline for UI / programmatic use.

Each function drives the same verified components used by the CLI entry points,
writes the standard ``data/`` artifacts, and returns structured Python data the
Streamlit app can render. Keeping this here keeps the UI thin and testable.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.agents.news_filter_agent import NewsFilterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.writer_agent import WriterAgent
from src.database.db_manager import DatabaseManager
from src.evaluation.evaluator import FilterEvaluator
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.models.article import Article
from src.orchestration.orchestrator import FetchOrchestrator
from src.skills.search_skill import SearchSkill
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer

# Standard artifact locations (match the CLI pipelines).
ARTICLES_DIR = "data/articles"
ALL_ARTICLES_MD = "data/articles/all_articles.md"
FILTER_INPUT_MD = "data/articles/_ui_filter_input.md"
FILTERED_MD = "data/context/filtered_articles.md"
SUMMARY_MD = "data/context/summary.md"
NEWSLETTER_MD = "data/output/newsletter.md"
GOLDEN_DATASET = "data/evaluation/golden_dataset.json"
EVAL_REPORT_MD = "data/evaluation/evaluation_report.md"

SOURCE_LABELS = {
    "HackerNews": "hackernews",
    "RSS": "rss",
    "GitHub Trending": "github_trending",
}


def article_to_row(article: Article) -> dict[str, Any]:
    """Flatten an Article into a display-friendly row."""
    return {
        "title": article.title,
        "source": article.source,
        "score": article.score,
        "published": article.published_at.strftime("%Y-%m-%d %H:%M"),
        "url": article.url,
    }


async def fetch_articles(
    sources: list[str],
    hn_limit: int = 15,
    rss_feed: str = "https://hnrss.org/frontpage",
    persist_to_db: bool = True,
) -> list[Article]:
    """Fetch from the selected sources, save markdown, optionally persist to DB."""
    transformer = ArticleTransformer()
    storage = MarkdownStorage(ARTICLES_DIR)

    fetchers = []
    if "HackerNews" in sources:
        fetchers.append(HackerNewsFetcher(transformer, storage, limit=hn_limit))
    if "RSS" in sources:
        fetchers.append(RSSFetcher(rss_feed, transformer, storage))
    if "GitHub Trending" in sources:
        fetchers.append(GitHubTrendingFetcher(transformer, storage))

    if not fetchers:
        return []

    orchestrator = FetchOrchestrator(fetchers, storage)
    articles = await orchestrator.fetch_all()

    if persist_to_db and articles:
        await save_to_database(articles)

    return articles


async def save_to_database(articles: list[Article]) -> int:
    """Insert articles into SQLite; return the total row count afterwards."""
    db = DatabaseManager()
    await db.initialize()
    for article in articles:
        await db.insert_article(
            {
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at.isoformat(),
                "summary": article.summary,
                "score": article.score,
            }
        )
    rows = await db.query_articles(limit=10000)
    return len(rows)


async def filter_articles(
    articles: list[Article], max_articles: int, model: str | None = None
) -> dict[str, Any]:
    """Run NewsFilterAgent over the first ``max_articles`` and parse the output."""
    subset = articles[:max_articles]
    storage = MarkdownStorage(ARTICLES_DIR)
    storage.save(subset, Path(FILTER_INPUT_MD).name)

    agent = NewsFilterAgent(model=model)
    await agent.execute(FILTER_INPUT_MD, FILTERED_MD)

    markdown = Path(FILTERED_MD).read_text(encoding="utf-8")
    return {
        "markdown": markdown,
        "kept": _parse_int(markdown, r"\*\*Total Output:\*\*\s*(\d+)"),
        "considered": _parse_int(markdown, r"\*\*Total Input:\*\*\s*(\d+)"),
        "articles": _parse_filtered(markdown),
        "path": FILTERED_MD,
    }


async def summarize(model: str | None = None) -> str:
    """Run SummarizerAgent on the filtered articles; return the summary markdown."""
    await SummarizerAgent(model=model).execute(FILTERED_MD, SUMMARY_MD)
    return Path(SUMMARY_MD).read_text(encoding="utf-8")


async def write_newsletter(model: str | None = None) -> str:
    """Run WriterAgent on the summary; return the newsletter markdown."""
    await WriterAgent(model=model).execute(SUMMARY_MD, NEWSLETTER_MD)
    return Path(NEWSLETTER_MD).read_text(encoding="utf-8")


async def search(query: str, limit: int = 10) -> dict[str, Any]:
    """Search the article database via the MCP-backed SearchSkill."""
    return await SearchSkill().search(query, limit=limit)


async def evaluate(model: str | None = None) -> dict[str, Any]:
    """Run the filter evaluation against the golden dataset."""
    evaluator = FilterEvaluator(GOLDEN_DATASET)
    if model:
        evaluator.agent = NewsFilterAgent(model=model)
    evaluation = await evaluator.evaluate()
    await evaluator.save_report(evaluation, EVAL_REPORT_MD)
    return evaluation


# ---- small parsing helpers ----------------------------------------------


def _parse_int(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0


def _parse_filtered(markdown: str) -> list[dict[str, Any]]:
    """Extract per-article rows from a filtered_articles.md document."""
    rows: list[dict[str, Any]] = []
    for section in markdown.split("\n---"):
        title_match = re.search(r"##\s+(.+)", section)
        if not title_match:
            continue
        score_match = re.search(r"\*\*Relevance Score:\*\*\s*(\d+)", section)
        reason_match = re.search(r"\*\*Reasoning:\*\*\s*(.+)", section)
        topics_match = re.search(r"\*\*Key Topics:\*\*\s*(.+)", section)
        url_match = re.search(r"\*\*URL:\*\*\s*(.+)", section)
        rows.append(
            {
                "title": title_match.group(1).strip(),
                "score": int(score_match.group(1)) if score_match else 0,
                "reasoning": reason_match.group(1).strip() if reason_match else "",
                "topics": topics_match.group(1).strip() if topics_match else "",
                "url": url_match.group(1).strip() if url_match else "",
            }
        )
    return rows
