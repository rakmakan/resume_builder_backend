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
        output: JobFinderOutput = await job_finder.run(profile=ctx.state.profile)
        ctx.state.postings = output.postings
        return Evaluate()


@dataclass
class Evaluate(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> 'Upskill' | End[State]:
        if not ctx.state.postings:
            return End(ctx.state)
        ctx.state.analysis = await evaluator.run(
            profile=ctx.state.profile, postings=ctx.state.postings
        )
        return Upskill()


@dataclass
class Upskill(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> End[State]:
        if ctx.state.analysis is None:
            return End(ctx.state)
        ctx.state.plan = await upskiller.run(analysis=ctx.state.analysis)
        return End(ctx.state)


graph = Graph(nodes=(FindJobs, Evaluate, Upskill))
