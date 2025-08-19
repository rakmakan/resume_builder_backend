"""Agent that recommends upskilling resources for identified gaps."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.models import GapAnalysis, UpskillPlan
from app.mcp import fetch
from app import get_logger

logger = get_logger(__name__)


class UpskillerInput(BaseModel):
    """Inputs required for the upskilling agent."""

    analysis: GapAnalysis


upskiller = Agent(
    model=TestModel(call_tools=[]),
    toolsets=[fetch] if fetch else [],
    output_type=UpskillPlan,
    system_prompt=(
        "Recommend courses, projects, and certifications based on the gap "
        "analysis. Use fetch_* tools to retrieve course information when "
        "necessary."
    ),
)

if fetch:
    logger.info("Upskiller agent configured with Fetch MCP server")
else:  # pragma: no cover - offline mode
    logger.info("Upskiller agent running without Fetch MCP server")
