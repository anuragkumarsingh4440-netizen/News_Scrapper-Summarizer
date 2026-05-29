"""Complete multi-agent pipeline (Milestone 4).

Fetch → persist to SQLite → Filter → Summarize → Write newsletter.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from src.agents.news_filter_agent import NewsFilterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.writer_agent import WriterAgent
from src.database.db_manager import DatabaseManager
from src.orchestration.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage


async def run_complete_pipeline() -> None:
    print("=" * 70)
    print("  Complete AI Agent Pipeline with MCP")
    print("=" * 70)

    # 1. Fetch
    print("\n📰 Step 1: Fetching articles...")
    orchestrator = FetchOrchestrator.with_defaults(storage=MarkdownStorage())
    articles = await orchestrator.fetch_all()
    fetch_output = Path("data/articles/all_articles.md")
    print(f"✅ Fetched {len(articles)} articles → {fetch_output}")

    # 2. Persist to database
    print("\n💾 Step 2: Saving to database...")
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
    db_articles = await db.query_articles(limit=1000)
    print(f"✅ Database has {len(db_articles)} articles")

    # 3. Filter
    print("\n🤖 Step 3: Filtering with AI agent...")
    filter_output = Path("data/context/filtered_articles.md")
    await NewsFilterAgent().execute(str(fetch_output), str(filter_output))

    # 4. Summarize
    print("\n📝 Step 4: Summarizing...")
    summary_output = Path("data/context/summary.md")
    await SummarizerAgent().execute(str(filter_output), str(summary_output))

    # 5. Write
    print("\n✍️  Step 5: Writing newsletter...")
    newsletter_output = Path("data/output/newsletter.md")
    await WriterAgent().execute(str(summary_output), str(newsletter_output))

    print("\n" + "=" * 70)
    print("🎉 Complete Pipeline Success!")
    print("=" * 70)
    print(f"   1. Fetched:    {len(articles)} articles")
    print(f"   2. Database:   {len(db_articles)} total articles")
    print(f"   3. Filtered:   {filter_output}")
    print(f"   4. Summary:    {summary_output}")
    print(f"   5. Newsletter: {newsletter_output}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_complete_pipeline())
