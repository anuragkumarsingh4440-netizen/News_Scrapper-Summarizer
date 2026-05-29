"""Fetch → Filter pipeline (Milestone 3).

Runs the orchestrator, then the NewsFilterAgent over the combined output.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from src.agents.news_filter_agent import NewsFilterAgent
from src.orchestration.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage


async def run_pipeline() -> None:
    print("=" * 60)
    print("  Pipeline: Fetch + Filter")
    print("=" * 60)

    print("\n📰 Step 1: Fetching articles...")
    orchestrator = FetchOrchestrator.with_defaults(storage=MarkdownStorage())
    articles = await orchestrator.fetch_all()
    fetch_output = Path("data/articles/all_articles.md")
    print(f"✅ Fetched {len(articles)} articles → {fetch_output}")

    print("\n🤖 Step 2: Filtering with AI...")
    agent = NewsFilterAgent()
    filter_output = Path("data/context/filtered_articles.md")
    await agent.execute(str(fetch_output), str(filter_output))

    print("\n" + "=" * 60)
    print("🎉 Pipeline complete!")
    print(f"   Fetched:  {fetch_output}")
    print(f"   Filtered: {filter_output}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
