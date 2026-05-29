"""Database MCP server — exposes the article database as MCP tools.

Tools:
* ``query_articles`` — list articles, optionally filtered by source
* ``search_articles`` — keyword search across title + summary
* ``get_sources``    — distinct sources present in the database

Run standalone over stdio; agents/skills connect as MCP clients.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.database.db_manager import DatabaseManager

server = Server("database-server")
db_manager: DatabaseManager | None = None


async def init_db() -> None:
    global db_manager
    db_manager = DatabaseManager()
    # stdout is the MCP JSON-RPC transport — keep it clean. DatabaseManager
    # prints a status line on initialize, so send that to stderr instead.
    with contextlib.redirect_stdout(sys.stderr):
        await db_manager.initialize()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_articles",
            description="Query articles from the database with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Filter by source (e.g. 'hackernews', 'rss')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="search_articles",
            description="Search articles by keyword in title or summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (matched in title and summary)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_sources",
            description="Get the list of all sources present in the database",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if db_manager is None:
        await init_db()
    assert db_manager is not None

    if name == "query_articles":
        articles = await db_manager.query_articles(
            source=arguments.get("source"), limit=arguments.get("limit", 50)
        )
        payload = {"total": len(articles), "articles": articles[:10]}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "search_articles":
        query = arguments["query"].lower()
        limit = arguments.get("limit", 20)
        all_articles = await db_manager.query_articles(limit=1000)
        matches = [
            a
            for a in all_articles
            if query in a["title"].lower() or query in (a.get("summary") or "").lower()
        ]
        payload = {"total": len(matches), "query": query, "articles": matches[:limit]}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "get_sources":
        all_articles = await db_manager.query_articles(limit=1000)
        sources = sorted({a["source"] for a in all_articles})
        payload = {"sources": sources, "total": len(sources)}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    await init_db()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
