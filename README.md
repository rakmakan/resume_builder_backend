# Career Advisor Agent System

A lightweight multi-agent prototype that analyzes a candidate's résumé against the current job market and recommends upskilling resources.  
Agents are built with **PydanticAI** and orchestrated using **pydantic-graph**.  
A minimal **CLI** and optional **FastAPI** server are provided.

## Features
- **Job Finder** – fetches job listings via an MCP Fetch server and extracts required skills.
- **Evaluator** – compares market skills to the candidate profile and produces a gap analysis.
- **Upskiller** – suggests courses, projects, and certifications to close skill gaps.
- **CLI interface** – run the full pipeline from the terminal.

## Installation
This repository uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
poetry shell  # optional: activate virtualenv
```

If Poetry is unavailable you can install the runtime dependencies directly:

```bash
pip install "pydantic-ai-slim[mcp]" pydantic-graph httpx fastapi
```

## Running the CLI
Create a simple résumé file where each line is a skill. Then execute:

```bash
python -m app.cli path/to/resume.txt
```

The CLI loads the résumé, runs the graph, and prints a dictionary containing job postings, gap analysis, and an upskill plan.

## FastAPI Server (Optional)
An HTTP wrapper is provided in `app/server.py`:

```bash
uvicorn app.server:app --reload
```

POST a `CandidateProfile` JSON to `/analyze` to run the pipeline.

## Replacing the Test Model with a Real Model
The agents use `TestModel` from PydanticAI so the system works offline.  
To use a real LLM:

1. Install the provider SDK (e.g. `openai`).
2. Replace the `model=TestModel()` arguments in `app/agents/*.py` with the provider string, e.g.:
   ```python
   job_finder = Agent(
       model="openai:gpt-4o",
       toolsets=[fetch],
       output_type=JobFinderOutput,
       ...
   )
   ```
3. Provide the necessary API key via environment variable (`OPENAI_API_KEY` for OpenAI).
4. Ensure the MCP Fetch server is running and accessible (see below).

## MCP Fetch Server
Agents rely on an MCP server that exposes a `fetch` tool for retrieving web pages.

- Python stdio implementation:
  ```bash
  pip install mcp-server-fetch
  python -m mcp_server_fetch stdio
  ```
- or point `MCP_FETCH_URL` in `.env` to an HTTP/SSE endpoint.

The default configuration in `app/mcp.py` uses the local stdio variant.

## Testing
Run the unit tests and validate the project configuration:

```bash
poetry check
pytest -q
```

## Environment
Copy `.env.example` to `.env` and populate secrets as needed:

```env
OPENAI_API_KEY=your-openai-key
MCP_FETCH_URL=http://localhost:3001/sse
```

## Limitations
The repository focuses on scaffolding and uses stub implementations.  
Fetching real job listings and course data requires a running MCP Fetch server and an LLM provider.
