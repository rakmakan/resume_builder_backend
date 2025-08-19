"""Pydantic models for the Career Advisor system."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class JobPosting(BaseModel):
    """Representation of a job listing scraped from the web."""

    title: str
    company: str
    location: Optional[str] = None
    url: str
    summary: str
    required_skills: List[str]
    years_experience: Optional[str] = None
    salary: Optional[str] = None


class CandidateProfile(BaseModel):
    """Basic candidate résumé information."""

    name: str
    years_experience: Optional[int]
    skills: List[str]


class Gap(BaseModel):
    """Missing skill relative to market demand."""

    skill: str
    importance: int = Field(ge=1, le=5)
    severity: str  # "dealbreaker" | "nice-to-have"


class GapAnalysis(BaseModel):
    """Summary of how well a candidate matches the market."""

    market_alignment: float  # 0..1
    matched_skills: List[str]
    missing: List[Gap]


class UpskillItem(BaseModel):
    """A concrete recommendation for improving a skill gap."""

    kind: str  # "course" | "project" | "cert"
    title: str
    provider: Optional[str]
    url: str
    rationale: str


class UpskillPlan(BaseModel):
    """Plan comprising multiple upskill items and a suggested timeline."""

    items: List[UpskillItem]
    timeline_weeks: int
