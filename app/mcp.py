"""MCP server client definitions for the Career Advisor system."""
from __future__ import annotations

from pydantic_ai.mcp import MCPServerSSE, MCPServerStdio

# Server accessible via Server-Sent Events/HTTP
fetch_sse = MCPServerSSE(url="http://localhost:3001/sse", tool_prefix="fetch")

# Local stdio subprocess variant
fetch_stdio = MCPServerStdio(
    command="python",
    args=["-m", "mcp_server_fetch", "stdio"],
    tool_prefix="fetch",
)

# Default export used by agents; change to fetch_sse if using network server
fetch = fetch_stdio
