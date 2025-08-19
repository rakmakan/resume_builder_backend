"""Agent responsible for locating jobs and extracting skills."""
from __future__ import annotations

from typing import List
from urllib.parse import quote_plus

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from app.models import JobPosting, CandidateProfile
from app.mcp import fetch
from app import get_logger

logger = get_logger(__name__)


class JobFinderOutput(BaseModel):
    """Structured output for the Job Finder agent."""

    roles: List[str]
    postings: List[JobPosting]


# Templates for search URLs across banking career sites and aggregators.
BANK_CAREER_PAGES = {
    "JPMorgan Chase": "https://careers.jpmorgan.com/us/en/search-results?keywords={query}",
    "Bank of America": "https://careers.bankofamerica.com/en-us/job-search?keywords={query}",
    "Citigroup": "https://jobs.citi.com/job-search-results/?keyword={query}",
    "Wells Fargo": "https://www.wellsfargojobs.com/search-jobs/{query}/0/0/1/",
    "Goldman Sachs": "https://www.goldmansachs.com/careers/jobsearch.html?search={query}",
}
LINKEDIN_TEMPLATE = (
    "https://www.linkedin.com/jobs/search/?keywords={query}%20{company}"
)
INDEED_TEMPLATE = "https://www.indeed.com/jobs?q={query}+{company}"


def build_search_urls(role: str) -> List[str]:
    """Return a list of job search URLs for major banks and aggregators."""
    query = quote_plus(role)
    urls: List[str] = []
    for company, career_tpl in BANK_CAREER_PAGES.items():
        company_q = quote_plus(company)
        urls.append(career_tpl.format(query=query))
        urls.append(LINKEDIN_TEMPLATE.format(query=query, company=company_q))
        urls.append(INDEED_TEMPLATE.format(query=query, company=company_q))
    return urls

system_prompt = (
    "Search real job openings at major banking companies. Use the 'search_jobs' tool to "
    "collect career-page, LinkedIn, and Indeed URLs, then fetch each page with 'fetch_url' "
    "and extract structured JobPosting objects. Return tightly structured postings."
    if fetch
    else "Web access is disabled; infer likely job postings from the candidate profile."
)

if fetch:
    logger.info("Job Finder agent configured with Fetch MCP server")
else:  # pragma: no cover - offline mode
    logger.info("Job Finder agent running without Fetch MCP server")

job_finder = Agent(
    model=TestModel(call_tools=[]),
    toolsets=[fetch] if fetch else [],
    output_type=JobFinderOutput,
    system_prompt=system_prompt,
)


if fetch:

    @job_finder.tool
    async def search_jobs(ctx: RunContext[CandidateProfile], role: str) -> List[str]:
        """Return URLs for banking, LinkedIn, and Indeed job searches."""
        urls = build_search_urls(role)
        logger.info("Generated %d search URLs for role '%s'", len(urls), role)
        return urls

    @job_finder.tool
    async def fetch_url(ctx: RunContext[CandidateProfile], url: str) -> str:
        """Fetch a URL via the MCP fetch server and return markdown content."""
        # Delegate the actual HTTP retrieval to the MCP fetch toolset attached to
        # the agent. The tool name is prefixed with ``fetch`` in ``mcp.py``.
        logger.info("Fetching URL via MCP: %s", url)
        return await ctx.tool("fetch.fetch", url=url)
