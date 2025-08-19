"""Agent responsible for locating jobs and extracting skills."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from app.models import JobPosting, CandidateProfile
from app.mcp import fetch


class JobFinderOutput(BaseModel):
    """Structured output for the Job Finder agent."""

    roles: List[str]
    postings: List[JobPosting]


job_finder = Agent(
    model=TestModel(call_tools=[]),
    toolsets=[fetch] if fetch else [],
    output_type=JobFinderOutput,
    system_prompt=(
        "You find relevant jobs from web pages fetched via the 'fetch_*' tools. "
        "Return tightly structured postings. Prefer official job pages."
    ),
)


@job_finder.tool
async def fetch_url(ctx: RunContext[CandidateProfile], url: str) -> str:
    """Fetch a URL via the MCP fetch server and return markdown content."""
    if fetch is None:
        raise RuntimeError("Fetch MCP server not configured")
    # Delegate the actual HTTP retrieval to the MCP fetch toolset attached to
    # the agent. The tool name is prefixed with ``fetch`` in ``mcp.py``.
    return await ctx.tool("fetch.fetch", url=url)
