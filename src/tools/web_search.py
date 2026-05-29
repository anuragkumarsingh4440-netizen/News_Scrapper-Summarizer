"""Web search tool (mocked) for LLM function calling.

Returns deterministic mock results so the curriculum doesn't require a paid
search API. The schema and call signature match what a real search tool would
expose, so swapping in a real backend later is a drop-in change.
"""

from __future__ import annotations

from typing import Any


def web_search(query: str, num_results: int = 3) -> dict[str, Any]:
    """Return mock search results for ``query``."""
    results = [
        {
            "title": f"Result {i + 1} for: {query}",
            "url": f"https://example.com/search?q={query}&r={i + 1}",
            "snippet": f"This is a mock search result for '{query}'.",
        }
        for i in range(max(1, num_results))
    ]
    return {
        "success": True,
        "query": query,
        "num_results": num_results,
        "results": results,
    }


# OpenAI / LiteLLM tool schema.
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information. Use when you need real-time data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    print(web_search("latest AI news"))
