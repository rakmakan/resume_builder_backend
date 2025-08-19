from app.mcp import fetch
from app.agents.job_finder import job_finder


def test_fetch_tool_not_registered_when_disabled():
    assert fetch is None
    assert job_finder._function_toolset.tools == {}
