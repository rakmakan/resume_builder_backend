"""Agent that recommends upskilling resources for identified gaps."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.models import GapAnalysis, UpskillPlan
from app.mcp import fetch


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
