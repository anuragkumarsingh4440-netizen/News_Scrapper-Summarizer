"""Simple MCP client for manually exercising the servers over stdio."""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_hello_server() -> None:
    """Connect to the hello-world server and call its tools."""
    print("🔌 Connecting to hello-world server...")
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "src.mcp_servers.hello_server"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("\n📋 Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            result = await session.call_tool("greet", {"name": "Alice"})
            print(f"\n   greet -> {result.content[0].text}")

            result = await session.call_tool("add", {"a": 5, "b": 3})
            print(f"   add   -> {result.content[0].text}")

            print("\n✅ MCP communication working!")


if __name__ == "__main__":
    asyncio.run(test_hello_server())
