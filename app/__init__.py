"""Career Advisor Agent System package with logging instrumentation."""
from __future__ import annotations

import logging

try:  # optional dependency for structured tracing
    import logfire as _logfire
except Exception:  # pragma: no cover - logfire not installed
    _logfire = None
else:  # pragma: no cover - side-effect configuration
    _logfire.configure()
    _logfire.instrument_pydantic_ai()

logging.basicConfig(level=logging.INFO)

# re-export logfire for other modules to use
logfire = _logfire

__all__ = [
    "models",
    "agents",
    "graph",
    "deps",
    "mcp",
    "server",
]
