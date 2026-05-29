"""Main entry point for the news fetcher (Milestones 1–2).

Wires up dependencies explicitly (dependency injection) and runs the
orchestrator. Run with::

    python -m src.main
"""

from __future__ import annotations

import asyncio
import sys

from src.orchestration.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage


async def main() -> int:
    print("=" * 60)
    print("  AI Upskill Project — News Fetcher")
    print("=" * 60)

    try:
        storage = MarkdownStorage("data/articles")
        orchestrator = FetchOrchestrator.with_defaults(storage=storage)
        articles = await orchestrator.fetch_all()

        print("\n" + "=" * 60)
        print(f"✅ Success! Fetched {len(articles)} articles total")
        print("📁 Saved to: data/articles/all_articles.md")
        print("=" * 60)
        return 0
    except Exception as exc:  # pragma: no cover - top-level guard
        import traceback

        print(f"\n❌ Error: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
