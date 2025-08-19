import asyncio
from pathlib import Path

from app.cli import run_pipeline


def test_pipeline_executes(tmp_path: Path):
    resume = tmp_path / "resume.txt"
    resume.write_text("python\naws")
    state = asyncio.run(run_pipeline(resume))
    assert state.postings is not None
