"""Agent that summarizes filtered articles into a topic-grouped digest."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent


class SummarizerAgent(BaseAgent):
    """Groups filtered articles by topic and writes a short summary per topic."""

    async def _load_context(self, input_path: str) -> dict[str, Any]:
        print(f"📖 Loading filtered articles from {input_path}")
        content = Path(input_path).read_text(encoding="utf-8")
        articles = self._parse_markdown(content)
        print(f"   Found {len(articles)} filtered articles")
        return {"articles": articles}

    @staticmethod
    def _parse_markdown(content: str) -> list[dict]:
        articles: list[dict] = []
        for section in content.split("\n---"):
            title_match = re.search(r"##\s+(.+)", section)
            if not title_match:
                continue
            title = title_match.group(1).strip()

            score_match = re.search(r"\*\*Relevance Score:\*\*\s*(\d+)", section)
            relevance = int(score_match.group(1)) if score_match else 0

            reason_match = re.search(r"\*\*Reasoning:\*\*\s*(.+)", section)
            reasoning = reason_match.group(1).strip() if reason_match else ""

            topics_match = re.search(r"\*\*Key Topics:\*\*\s*(.+)", section)
            topics = topics_match.group(1).strip() if topics_match else ""

            articles.append(
                {
                    "title": title,
                    "relevance": relevance,
                    "reasoning": reasoning,
                    "topics": topics,
                }
            )
        return articles

    async def _process(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context["articles"]
        print(f"📝 Summarizing {len(articles)} articles...")

        grouped: dict[str, list[dict]] = {}
        for article in articles:
            topic = article["topics"].split(",")[0] if article["topics"] else "Other"
            topic = topic.strip() or "Other"
            grouped.setdefault(topic, []).append(article)

        summaries: dict[str, str] = {}
        for topic, topic_articles in grouped.items():
            print(f"   Summarizing {topic}: {len(topic_articles)} articles")
            summaries[topic] = self._summarize_topic(topic, topic_articles)

        return {
            "topics": grouped,
            "summaries": summaries,
            "total_articles": len(articles),
        }

    def _summarize_topic(self, topic: str, articles: list[dict]) -> str:
        articles_text = "\n".join(f"- {a['title']}: {a['reasoning']}" for a in articles)
        prompt = (
            f"Summarize these {topic} articles into 2-3 sentences for a daily "
            f"digest:\n\n{articles_text}\n\n"
            "Focus on the main themes and key developments. Be concise."
        )
        return self._call_llm(prompt).strip()

    async def _save_result(self, result: dict[str, Any], output_path: str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write("# AI/ML Daily Digest - Summary\n\n")
            f.write(f"**Total Articles:** {result['total_articles']}\n\n")
            for topic, summary in result["summaries"].items():
                count = len(result["topics"][topic])
                f.write(f"## {topic} ({count} articles)\n\n")
                f.write(f"{summary}\n\n")
                f.write("---\n\n")
        print(f"💾 Saved summary to {out}")
