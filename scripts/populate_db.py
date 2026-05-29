#!/usr/bin/env python3
"""Populate the SQLite database from saved markdown article files.

Run from the repo root after fetching::

    python scripts/populate_db.py
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path

from src.database.db_manager import DatabaseManager


async def populate_from_markdown() -> None:
    db = DatabaseManager()
    await db.initialize()

    articles_dir = Path("data/articles")
    if not articles_dir.exists():
        print("⚠️  data/articles/ not found — run `python -m src.main` first.")
        return

    for md_file in articles_dir.glob("*.md"):
        print(f"Reading {md_file.name}...")
        content = md_file.read_text(encoding="utf-8")

        for section in content.split("\n---"):
            title_match = re.search(r"##\s+(.+)", section)
            url_match = re.search(r"\*\*URL:\*\*\s*(.+)", section)
            if not title_match or not url_match:
                continue

            source_match = re.search(r"\*\*Source:\*\*\s*(.+)", section)
            body_lines = [
                line.strip()
                for line in section.splitlines()
                if line.strip()
                and not line.lstrip().startswith("**")
                and not line.lstrip().startswith("#")
            ]
            await db.insert_article(
                {
                    "title": title_match.group(1).strip(),
                    "url": url_match.group(1).strip(),
                    "source": source_match.group(1).strip()
                    if source_match
                    else "unknown",
                    "published_at": datetime.now().isoformat(),
                    "summary": body_lines[-1] if body_lines else "",
                }
            )

    articles = await db.query_articles(limit=1000)
    print(f"\n✅ Database populated with {len(articles)} articles")


if __name__ == "__main__":
    asyncio.run(populate_from_markdown())
