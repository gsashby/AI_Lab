"""Tracing bootstrap — LangSmith today, kept swappable for later.

Design note: everything the rest of the lab needs goes through `setup_tracing`
and the `traceable` re-export below. If you later move to Langfuse or an
OpenTelemetry pipeline (see the plan's Track 4), you change this one file and
nothing else in the lab has to know.

LangSmith is driven almost entirely by environment variables. LangChain /
LangGraph auto-instrument when LANGSMITH_TRACING=true and a key is present, so
this function's main job is to make the env consistent and fail *soft* (warn,
don't crash) when a key is missing — a learning lab should still run without a
tracing account.
"""

from __future__ import annotations

import os
import warnings

_CONFIGURED = False


def setup_tracing(settings) -> bool:
    """Configure LangSmith tracing from settings. Returns True if tracing is active.

    Idempotent: safe to call multiple times (config.py calls it at import).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return os.environ.get("LANGSMITH_TRACING") == "true"

    if not settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "false"
        _CONFIGURED = True
        return False

    if not settings.langsmith_api_key:
        warnings.warn(
            "LANGSMITH_TRACING is on but LANGSMITH_API_KEY is not set. "
            "Running WITHOUT tracing. Add a key from https://smith.langchain.com "
            "to see runs in the LangSmith UI.",
            stacklevel=2,
        )
        os.environ["LANGSMITH_TRACING"] = "false"
        _CONFIGURED = True
        return False

    # Export the canonical env vars LangChain/LangGraph read.
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    _CONFIGURED = True
    return True


def tracing_active() -> bool:
    """True if tracing is currently enabled in the process environment."""
    return os.environ.get("LANGSMITH_TRACING") == "true"


try:  # Re-export so tracks decorate plain functions without importing langsmith directly.
    from langsmith import traceable
except Exception:  # pragma: no cover - langsmith optional at import time

    def traceable(*args, **kwargs):  # type: ignore
        """No-op fallback so code using @traceable still runs if langsmith is absent."""
        def _decorator(fn):
            return fn

        # Support both @traceable and @traceable(name="...")
        if args and callable(args[0]):
            return args[0]
        return _decorator


__all__ = ["setup_tracing", "tracing_active", "traceable"]
