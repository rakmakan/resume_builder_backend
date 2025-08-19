"""Agent that evaluates candidate skills against market demand."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.models import CandidateProfile, JobPosting, GapAnalysis
from app import get_logger
import logfire

logfire.configure(scrubbing=False)  
logfire.instrument_pydantic_ai()

logger = get_logger(__name__)


class EvaluatorInput(BaseModel):
    """Inputs required for the evaluator."""

    profile: CandidateProfile
    postings: List[JobPosting]


evaluator = Agent(
    model="openai:gpt-4o-mini",
    output_type=GapAnalysis,
    system_prompt=(
        "Compare the candidate's skills with requirements across job postings "
        "and return a structured gap analysis."
    ),
)

logger.info("Evaluator agent initialized")
