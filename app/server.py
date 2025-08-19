"""FastAPI server exposing the Career Advisor pipeline."""
from __future__ import annotations

from fastapi import FastAPI

from app.graph import State, graph
from app.models import CandidateProfile
from app import logfire, get_logger

logger = get_logger(__name__)

app = FastAPI(title="Career Advisor Agent System")

if logfire:  # pragma: no cover - optional instrumentation
    logfire.instrument_fastapi(app)


@app.post("/analyze")
async def analyze(profile: CandidateProfile) -> State:
    """Run the full agent graph for a given candidate profile."""
    logger.info("Received analysis request for %s", profile.name)
    run = await graph.run(State(profile=profile))
    logger.info("Analysis pipeline complete")
    return run.state
