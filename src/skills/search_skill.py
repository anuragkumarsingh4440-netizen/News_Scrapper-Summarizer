"""Reusable search skill backed by the database MCP server.

A *skill* is a higher-level abstraction over raw MCP tools: callers just call
``search(query)`` and the skill handles connecting to the server, calling the
``search_articles`` tool, and parsing the response.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SearchSkill:
    """Searches articles via the database MCP server."""

    def __init__(self) -> None:
        # Launch the server as a module so `src` imports resolve.
        self.server_params = StdioServerParameters(
            command=sys.executable, args=["-m", "src.mcp_servers.database_server"]
        )

    async def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search for articles matching ``query``."""
        print(f"🔍 SearchSkill: searching for '{query}'...")
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "search_articles", {"query": query, "limit": limit}
                    )
                    data = json.loads(result.content[0].text)
                    print(f"   Found {data['total']} matches")
                    return {
                        "success": True,
                        "query": query,
                        "total": data["total"],
                        "articles": data["articles"],
                    }
        except Exception as exc:
            print(f"   ❌ Search failed: {exc}")
            return {
                "success": False,
                "query": query,
                "error": str(exc),
                "articles": [],
            }


if __name__ == "__main__":

    async def _demo() -> None:
        skill = SearchSkill()
        result = await skill.search("machine learning", limit=5)
        print(f"\n✅ success={result['success']} total={result.get('total')}")

    asyncio.run(_demo())
