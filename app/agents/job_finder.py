"""Agent responsible for locating jobs and extracting skills."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from app.models import JobPosting, CandidateProfile
from app.mcp import fetch
from app import get_logger

logger = get_logger(__name__)


class JobFinderOutput(BaseModel):
    """Structured output for the Job Finder agent."""

    roles: List[str]
    postings: List[JobPosting]


system_prompt = (
    "You find relevant jobs from web pages fetched via the 'fetch_*' tools. "
    "Return tightly structured postings. Prefer official job pages."
    if fetch
    else "Web access is disabled; infer likely job postings from the candidate profile."
)

if fetch:
    logger.info("Job Finder agent configured with Fetch MCP server")
else:  # pragma: no cover - offline mode
    logger.info("Job Finder agent running without Fetch MCP server")

job_finder = Agent(
    model=TestModel(call_tools=[]),
    toolsets=[fetch] if fetch else [],
    output_type=JobFinderOutput,
    system_prompt=system_prompt,
)


if fetch:

    @job_finder.tool
    async def fetch_url(ctx: RunContext[CandidateProfile], url: str) -> str:
        """Fetch a URL via the MCP fetch server and return markdown content."""
        # Delegate the actual HTTP retrieval to the MCP fetch toolset attached to
        # the agent. The tool name is prefixed with ``fetch`` in ``mcp.py``.
        logger.info("Fetching URL via MCP: %s", url)
        return await ctx.tool("fetch.fetch", url=url)
