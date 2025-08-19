"""MCP server client definitions for the Career Advisor system."""
from __future__ import annotations

import os
from pydantic_ai.mcp import MCPServerSSE, MCPServerStdio


def _build_fetch() -> MCPServerStdio | None:
    """Return an MCP Fetch server client if enabled via env var."""
    if os.getenv("ENABLE_FETCH"):
        return MCPServerStdio(
            command="python",
            args=["-m", "mcp_server_fetch", "stdio"],
            tool_prefix="fetch",
        )
    return None


# Default export; when ENABLE_FETCH is unset, no MCP toolset is used.
fetch = _build_fetch()
