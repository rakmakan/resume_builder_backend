"""Career Advisor Agent System package with logging instrumentation."""
from __future__ import annotations

import logging
import os

try:  # optional dependency for structured tracing
    import logfire as _logfire
except Exception:  # pragma: no cover - logfire not installed
    _logfire = None
else:  # pragma: no cover - side-effect configuration
    _logfire.configure(
        token=os.getenv("LOGFIRE_TOKEN"),
        service="career-advisor",
    )
    _logfire.instrument_pydantic_ai()
    try:  # instrument HTTPX when available
        _logfire.instrument_httpx()
    except Exception:  # pragma: no cover - optional
        pass

logging.basicConfig(level=logging.INFO)


def get_logger(name: str | None = None):
    """Return a logfire logger if configured, otherwise stdlib logger."""
    if _logfire is not None:
        return _logfire.get_logger(name)
    return logging.getLogger(name)


# re-export logfire for other modules to use
logfire = _logfire

__all__ = [
    "models",
    "agents",
    "graph",
    "deps",
    "mcp",
    "server",
    "get_logger",
]
