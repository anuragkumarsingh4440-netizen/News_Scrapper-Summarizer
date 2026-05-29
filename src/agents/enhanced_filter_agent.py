"""News filter agent with tool use.

Extends :class:`NewsFilterAgent` so the LLM can call a calculator or web search
while judging relevance. Demonstrates wiring tool schemas + their backing
functions into an agent.
"""

from __future__ import annotations

from src.agents.news_filter_agent import NewsFilterAgent
from src.tools.calculator import CALCULATOR_SCHEMA, calculator
from src.tools.web_search import WEB_SEARCH_SCHEMA, web_search


class EnhancedFilterAgent(NewsFilterAgent):
    """A filter agent that may call tools during judging."""

    def __init__(self) -> None:
        super().__init__(tools=[CALCULATOR_SCHEMA, WEB_SEARCH_SCHEMA])
        self.register_tool_function("calculator", calculator)
        self.register_tool_function("web_search", web_search)

    def _judge_relevance(self, article: dict) -> dict:
        prompt = f"""You are an AI/ML news analyst with access to tools.

Article:
Title: {article['title']}
Summary: {article.get('summary', '')}

Judge if this is AI/ML relevant. You may use:
- calculator: for any math calculations
- web_search: to verify claims or get context

Output ONLY valid JSON:
{{
  "relevant": true/false,
  "relevance_score": 1-10,
  "reasoning": "explanation (mention if you used tools)",
  "key_topics": ["topic1", "topic2"]
}}
"""
        try:
            response = self._call_llm_with_tools(prompt)
            return self._extract_json(response)
        except Exception as exc:
            print(f"      ⚠️  Error: {exc}")
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Error: {exc}",
                "key_topics": [],
            }
