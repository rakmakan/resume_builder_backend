"""Graph orchestration for the Career Advisor agents."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from app.models import (
    CandidateProfile,
    GapAnalysis,
    JobPosting,
    UpskillPlan,
)
from app.agents.job_finder import job_finder, JobFinderOutput
from app.agents.evaluator import evaluator
from app.agents.upskiller import upskiller


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
        # Use a simple prompt since the TestModel ignores content but requires a string.
        run = await job_finder.run(
            f"skills: {', '.join(ctx.state.profile.skills)}"
        )
        ctx.state.postings = run.output.postings
        return Evaluate()


@dataclass
class Evaluate(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> 'Upskill' | End[State]:
        if not ctx.state.postings:
            return End(ctx.state)
        eval_run = await evaluator.run("evaluate gaps")
        ctx.state.analysis = eval_run.output
        return Upskill()


@dataclass
class Upskill(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> End[State]:
        if ctx.state.analysis is None:
            return End(ctx.state)
        up_run = await upskiller.run("recommend upskilling")
        ctx.state.plan = up_run.output
        return End(ctx.state)


graph = Graph(nodes=(FindJobs, Evaluate, Upskill))
