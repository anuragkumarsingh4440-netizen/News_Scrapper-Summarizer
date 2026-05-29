"""Tests for NewsFilterAgent parsing/IO, using a stubbed LLM (no network)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.news_filter_agent import NewsFilterAgent

SAMPLE_MD = """# News Articles

## GPT-4 Released by OpenAI

**Source:** hackernews
**URL:** https://example.com/gpt4
**Published:** 2026-01-01 12:00
**Score:** 100

OpenAI announces GPT-4 with enhanced capabilities.

---

## New JavaScript Framework

**Source:** rss
**URL:** https://example.com/js
**Published:** 2026-01-01 12:00
**Score:** 5

A React alternative for web development.

---
"""


@pytest.fixture
def agent():
    # Provide an explicit model so construction doesn't depend on .env.
    return NewsFilterAgent(model="test/model")


def test_parse_markdown_extracts_articles(agent):
    articles = agent._parse_markdown(SAMPLE_MD)
    titles = [a["title"] for a in articles]
    assert "GPT-4 Released by OpenAI" in titles
    assert "New JavaScript Framework" in titles
    gpt = next(a for a in articles if a["title"].startswith("GPT-4"))
    assert gpt["url"] == "https://example.com/gpt4"


@pytest.mark.parametrize(
    "raw",
    [
        '{"relevant": true, "relevance_score": 9, "reasoning": "r", "key_topics": []}',
        '```json\n{"relevant": true, "relevance_score": 9, "reasoning": "r"}\n```',
        'Here is my answer:\n{"relevant": false, "relevance_score": 2, "reasoning": "r"}',
    ],
)
def test_extract_json_handles_formats(agent, raw):
    parsed = agent._extract_json(raw)
    assert "relevant" in parsed and "relevance_score" in parsed


def test_judge_relevance_parses_llm_output(agent):
    fake = '{"relevant": true, "relevance_score": 8, "reasoning": "LLM topic", "key_topics": ["LLM"]}'
    with patch.object(agent, "_call_llm", return_value=fake):
        judgment = agent._judge_relevance({"title": "GPT-5", "summary": "new model"})
    assert judgment["relevant"] is True
    assert judgment["relevance_score"] == 8


def test_judge_relevance_handles_bad_llm_output(agent):
    with patch.object(agent, "_call_llm", return_value="not json at all"):
        judgment = agent._judge_relevance({"title": "x", "summary": "y"})
    assert judgment["relevant"] is False
    assert judgment["relevance_score"] == 0


async def test_execute_end_to_end_with_stubbed_llm(agent, tmp_path):
    input_file = tmp_path / "in.md"
    output_file = tmp_path / "out.md"
    input_file.write_text(SAMPLE_MD, encoding="utf-8")

    def fake_llm(prompt, system=None):
        # Branch on the article's own Title line, not the few-shot examples
        # (which mention both titles).
        if "Title: GPT-4 Released by OpenAI" in prompt:
            return '{"relevant": true, "relevance_score": 10, "reasoning": "LLM", "key_topics": ["LLM"]}'
        return '{"relevant": false, "relevance_score": 1, "reasoning": "web", "key_topics": []}'

    with patch.object(agent, "_call_llm", side_effect=fake_llm):
        await agent.execute(str(input_file), str(output_file))

    content = Path(output_file).read_text(encoding="utf-8")
    assert "GPT-4 Released by OpenAI" in content
    assert "New JavaScript Framework" not in content


@pytest.mark.llm
async def test_filter_agent_live(tmp_path):
    """Live smoke test against the configured LLM. Run with: pytest -m llm"""
    agent = NewsFilterAgent()
    input_file = tmp_path / "in.md"
    output_file = tmp_path / "out.md"
    input_file.write_text(SAMPLE_MD, encoding="utf-8")
    await agent.execute(str(input_file), str(output_file))
    assert output_file.exists()
