"""FastAPI server exposing the Career Advisor pipeline."""
from __future__ import annotations

from fastapi import FastAPI

from app.graph import State, graph
from app.deps import load_resume
from app.models import CandidateProfile

app = FastAPI(title="Career Advisor Agent System")


@app.post("/analyze")
async def analyze(profile: CandidateProfile) -> State:
    """Run the full agent graph for a given candidate profile."""
    run = await graph.run(State(profile=profile))
    return run.state
