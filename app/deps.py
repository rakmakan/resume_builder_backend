"""Dependency helpers for the Career Advisor system."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.models import CandidateProfile


def load_resume(path: Path) -> CandidateProfile:
    """Load a résumé from a text file and produce a CandidateProfile.

    This is a tiny placeholder showing where dependency injection can occur.
    """

    text = path.read_text(encoding="utf8")
    skills = [line.strip() for line in text.splitlines() if line.strip()]
    return CandidateProfile(name="Unknown", years_experience=None, skills=skills)


# Example DI container placeholder
get_resume_loader: Callable[[Path], CandidateProfile] = load_resume
