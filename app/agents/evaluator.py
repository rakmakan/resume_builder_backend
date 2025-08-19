"""Agent that evaluates candidate skills against market demand."""
from __future__ import annotations

from typing import List
from collections import Counter

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.models import CandidateProfile, JobPosting, Gap, GapAnalysis
from app import get_logger

logger = get_logger(__name__)


class EvaluatorInput(BaseModel):
    """Inputs required for the evaluator."""

    profile: CandidateProfile
    postings: List[JobPosting]


evaluator = Agent(
    model=TestModel(),
    output_type=GapAnalysis,
    deps_type=EvaluatorInput,
    system_prompt=(
        "For each job posting, summarize the description and list required skills. "
        "Compare these skills with the candidate's résumé and return a GapAnalysis "
        "highlighting matched and missing skills.",
    ),
)


def analyze_gaps(profile: CandidateProfile, postings: List[JobPosting]) -> GapAnalysis:
    """Compute basic gap analysis without calling an LLM."""
    counts: Counter[str] = Counter()
    for post in postings:
        counts.update(skill.lower() for skill in post.required_skills)

    candidate_skills = {s.lower() for s in profile.skills}
    matched: List[str] = []
    missing: List[Gap] = []
    for skill, count in counts.items():
        if skill in candidate_skills:
            matched.append(skill)
        else:
            severity = "dealbreaker" if count == len(postings) else "nice-to-have"
            missing.append(Gap(skill=skill, importance=min(count, 5), severity=severity))

    market_alignment = len(matched) / (len(counts) or 1)
    return GapAnalysis(market_alignment=market_alignment, matched_skills=matched, missing=missing)


logger.info("Evaluator agent initialized")
