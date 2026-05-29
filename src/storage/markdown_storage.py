"""Markdown implementation of the ArticleStorage interface.

Single Responsibility: file I/O only. Knows nothing about where articles come
from or how they were transformed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.models.article import Article
from src.storage.base_storage import ArticleStorage


class MarkdownStorage(ArticleStorage):
    """Saves articles to markdown files under ``base_path``."""

    def __init__(self, base_path: str = "data/articles") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, articles: list[Article], filename: str | None = None) -> Path:
        """Write articles to a markdown file and return its path."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"articles_{timestamp}.md"

        filepath = self.base_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# News Articles\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Articles:** {len(articles)}\n\n")
            f.write("---\n\n")

            for article in articles:
                f.write(article.to_markdown())
                f.write("\n---\n\n")

        print(f"💾 Saved {len(articles)} articles to: {filepath}")
        return filepath


if __name__ == "__main__":
    storage = MarkdownStorage("data/test_articles")
    sample = Article(
        title="Test Article",
        url="http://test.com",
        published_at=datetime.now(),
        source="test",
        summary="Test summary",
    )
    path = storage.save([sample], "test.md")
    assert path.exists()
    print(f"✅ Saved to {path}")
