"""Graph orchestration for the Career Advisor agents."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from app import get_logger
from app.models import (
    CandidateProfile,
    GapAnalysis,
    JobPosting,
    UpskillPlan,
)
from app.agents.job_finder import job_finder, JobFinderOutput
from app.agents.evaluator import analyze_gaps
from app.agents.upskiller import upskiller


logger = get_logger(__name__)


@dataclass
class State:
    """Shared state flowing through the agent graph."""

    profile: CandidateProfile
    postings: list[JobPosting] | None = None
    analysis: GapAnalysis | None = None
    plan: UpskillPlan | None = None


@dataclass
class FindJobs(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> 'Evaluate':
        logger.info("Finding jobs for %s", ctx.state.profile.skills)
        run = await job_finder.run(
            f"skills: {', '.join(ctx.state.profile.skills)}"
        )
        ctx.state.postings = run.output.postings
        logger.info("Found %d postings", len(ctx.state.postings))
        return Evaluate()


@dataclass
class Evaluate(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> 'Upskill' | End[State]:
        if not ctx.state.postings:
            logger.info("No postings found; ending pipeline")
            return End(ctx.state)
        logger.info("Evaluating gaps across %d postings", len(ctx.state.postings))
        ctx.state.analysis = analyze_gaps(ctx.state.profile, ctx.state.postings)
        return Upskill()


@dataclass
class Upskill(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> End[State]:
        if ctx.state.analysis is None:
            logger.info("No analysis available; ending pipeline")
            return End(ctx.state)
        logger.info("Generating upskill plan")
        up_run = await upskiller.run("recommend upskilling")
        ctx.state.plan = up_run.output
        return End(ctx.state)


graph = Graph(nodes=(FindJobs, Evaluate, Upskill))
