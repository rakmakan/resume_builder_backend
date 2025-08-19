"""Command-line interface for the Career Advisor Agent System."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from pathlib import Path
from app import get_logger
from app.deps import load_resume
from app.graph import State, graph, FindJobs

logger = get_logger(__name__)


async def run_pipeline(resume_path: Path) -> State:
    """Execute the full agent graph for the given résumé file."""
    logger.info("Loading résumé from %s", resume_path)
    profile = load_resume(resume_path)
    result = await graph.run(FindJobs(), state=State(profile=profile))
    logger.info("Pipeline execution finished")
    return result.state


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Career Advisor agents on a résumé")
    parser.add_argument("resume", type=Path, help="Path to a text file containing résumé skills")
    args = parser.parse_args()

    state = asyncio.run(run_pipeline(args.resume))
    # Display results as plain dictionaries for readability
    print(asdict(state))


if __name__ == "__main__":
    main()
