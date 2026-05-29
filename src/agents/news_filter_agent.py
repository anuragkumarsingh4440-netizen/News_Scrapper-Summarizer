"""Agent that filters articles for AI/ML relevance.

Reads articles from a markdown file, asks the LLM to judge each one, and writes
the relevant ones (with score + reasoning) to a new markdown file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent


class NewsFilterAgent(BaseAgent):
    """Filters articles, keeping those judged AI/ML-relevant."""

    RELEVANCE_THRESHOLD = 6  # out of 10

    async def _load_context(self, input_path: str) -> dict[str, Any]:
        print(f"📖 Loading articles from {input_path}")
        content = Path(input_path).read_text(encoding="utf-8")
        articles = self._parse_markdown(content)
        print(f"   Found {len(articles)} articles")
        return {"articles": articles}

    @staticmethod
    def _parse_markdown(content: str) -> list[dict]:
        """Extract articles from a markdown document produced by storage/agents."""
        articles: list[dict] = []
        for section in content.split("\n---"):
            title_match = re.search(r"##\s+(.+)", section)
            if not title_match:
                continue
            title = title_match.group(1).strip()

            url_match = re.search(r"\*\*URL:\*\*\s*(.+)", section)
            url = url_match.group(1).strip() if url_match else ""

            # Summary: the last non-metadata, non-heading line in the section.
            body_lines = [
                line.strip()
                for line in section.splitlines()
                if line.strip()
                and not line.lstrip().startswith("**")
                and not line.lstrip().startswith("#")
            ]
            summary = body_lines[-1] if body_lines else ""

            articles.append({"title": title, "url": url, "summary": summary})
        return articles

    async def _process(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context["articles"]
        print(f"🔍 Filtering {len(articles)} articles...")

        filtered: list[dict] = []
        for i, article in enumerate(articles, start=1):
            print(f"   [{i}/{len(articles)}] {article['title'][:50]}...")
            judgment = self._judge_relevance(article)

            if (
                judgment["relevant"]
                and judgment["relevance_score"] >= self.RELEVANCE_THRESHOLD
            ):
                filtered.append(
                    {
                        **article,
                        "relevance_score": judgment["relevance_score"],
                        "reasoning": judgment["reasoning"],
                        "key_topics": judgment.get("key_topics", []),
                    }
                )
                print(f"      ✅ Relevant (score: {judgment['relevance_score']})")
            else:
                print(f"      ❌ Not relevant (score: {judgment['relevance_score']})")

        print(f"\n📊 Filtered: {len(filtered)}/{len(articles)} articles")
        return {
            "filtered_articles": filtered,
            "total_input": len(articles),
            "total_output": len(filtered),
        }

    def _judge_relevance(self, article: dict) -> dict:
        """Ask the LLM whether ``article`` is AI/ML-relevant; return parsed JSON."""
        prompt = f"""You are an expert AI/ML news analyst. Judge if this article is relevant to AI/ML.

Article:
Title: {article['title']}
Summary: {article.get('summary', '')}

Relevant topics include: Machine Learning, LLMs, Neural Networks, Computer Vision,
NLP, AI Research, AI Applications, Deep Learning, Transformers, GPT, Stable Diffusion,
AI Ethics, AI Safety.

Output ONLY valid JSON in this exact format:
{{
  "relevant": true or false,
  "relevance_score": 1-10,
  "reasoning": "brief explanation",
  "key_topics": ["topic1", "topic2"]
}}

Examples:
- "GPT-4 Released" -> {{"relevant": true, "relevance_score": 10, "reasoning": "Major LLM release", "key_topics": ["LLM", "GPT"]}}
- "New JavaScript Framework" -> {{"relevant": false, "relevance_score": 1, "reasoning": "Web dev, not AI", "key_topics": []}}

Your JSON response:"""

        try:
            response = self._call_llm(prompt)
            judgment = self._extract_json(response)
            # Validate required keys are present.
            assert "relevant" in judgment
            assert "relevance_score" in judgment
            assert "reasoning" in judgment
            return judgment
        except Exception as exc:
            print(f"      ⚠️  Failed to parse LLM response: {exc}")
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {exc}",
                "key_topics": [],
            }

    @staticmethod
    def _extract_json(response: str) -> dict:
        """Pull a JSON object out of a possibly fenced/explained LLM response."""
        text = response.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        else:
            # Fall back to the first {...} block.
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                text = match.group(0)
        return json.loads(text.strip())

    async def _save_result(self, result: dict[str, Any], output_path: str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        articles = result["filtered_articles"]
        total_in = result["total_input"] or 1

        with open(out, "w", encoding="utf-8") as f:
            f.write("# Filtered AI/ML Articles\n\n")
            f.write(f"**Total Input:** {result['total_input']}\n")
            f.write(f"**Total Output:** {result['total_output']}\n")
            f.write(
                f"**Filter Rate:** {result['total_output'] / total_in * 100:.1f}%\n\n"
            )
            f.write("---\n\n")
            for article in articles:
                f.write(f"## {article['title']}\n\n")
                f.write(f"**URL:** {article['url']}\n")
                f.write(f"**Relevance Score:** {article['relevance_score']}/10\n")
                f.write(f"**Reasoning:** {article['reasoning']}\n")
                f.write(f"**Key Topics:** {', '.join(article['key_topics'])}\n\n")
                f.write(f"{article['summary']}\n\n")
                f.write("---\n\n")

        print(f"💾 Saved {len(articles)} filtered articles to {out}")
