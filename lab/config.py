"""Central configuration for the lab.

This module does three jobs:

1. Loads settings from the environment (and a local `.env`) via pydantic-settings.
2. Defines a MODEL_REGISTRY so any track can request a model by a stable name
   (e.g. "anthropic-default") instead of hard-coding provider details. This is
   what lets orchestration nodes swap providers per-node and what feeds the
   model-matrix evals in Phase 4.
3. Bootstraps observability so tracing is *on by default* the moment the package
   is imported. (See lab/observability/tracing.py.)

Anthropic is prioritized: LAB_DEFAULT_MODEL defaults to "anthropic-default".
OpenAI entries are registered and ready for future learning.
"""

from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env before Settings reads the environment.
load_dotenv()


class Settings(BaseSettings):
    """Environment-backed settings. Unset keys are fine until a model is used."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Provider keys (optional at import time; validated lazily when a model is built)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Default registry entry to use when a caller doesn't specify one.
    lab_default_model: str = "anthropic-default"

    # LangSmith / tracing
    langsmith_tracing: bool = True
    langsmith_api_key: str | None = None
    langsmith_project: str = "ai-lab"
    langsmith_endpoint: str | None = None


settings = Settings()


@dataclass(frozen=True)
class ModelSpec:
    """A provider-agnostic description of a model the lab can build."""

    provider: str  # "anthropic" | "openai"
    model: str  # provider model id
    temperature: float = 0.0
    max_tokens: int = 1024


# Stable names -> concrete model specs. Update model ids here in one place.
# Anthropic first (default); OpenAI registered for future learning.
MODEL_REGISTRY: dict[str, ModelSpec] = {
    "anthropic-default": ModelSpec("anthropic", "claude-sonnet-4-5", temperature=0.0),
    "anthropic-fast": ModelSpec("anthropic", "claude-haiku-4-5", temperature=0.0),
    "openai-default": ModelSpec("openai", "gpt-4.1", temperature=0.0),
    "openai-fast": ModelSpec("openai", "gpt-4.1-mini", temperature=0.0),
}


def describe_registry() -> str:
    """Human-readable summary used by `make check` to confirm setup without API calls."""
    from lab.observability.tracing import tracing_active

    lines = ["ai-lab configuration", "=" * 20]
    lines.append(f"default model : {settings.lab_default_model}")
    if tracing_active():
        lines.append(f"tracing       : on (project: {settings.langsmith_project})")
    elif settings.langsmith_tracing:
        lines.append("tracing       : requested but INACTIVE (LANGSMITH_API_KEY not set)")
    else:
        lines.append("tracing       : off")
    have = {
        "anthropic": bool(settings.anthropic_api_key),
        "openai": bool(settings.openai_api_key),
    }
    lines.append("")
    lines.append("registry:")
    for name, spec in MODEL_REGISTRY.items():
        key_ok = "key ✓" if have.get(spec.provider) else "key ✗ (set to use)"
        default = "  <-- default" if name == settings.lab_default_model else ""
        lines.append(f"  {name:18} {spec.provider}:{spec.model:22} {key_ok}{default}")
    return "\n".join(lines)


def get_model(name: str | None = None):
    """Build a LangChain chat model from a registry name.

    Imports of provider packages are deferred so that merely importing `lab`
    (e.g. for `make check`) never requires the provider SDKs or API keys.
    """
    name = name or settings.lab_default_model
    if name not in MODEL_REGISTRY:
        raise KeyError(
            f"Unknown model '{name}'. Known: {', '.join(MODEL_REGISTRY)}"
        )
    spec = MODEL_REGISTRY[name]

    if spec.provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set (needed for '%s')." % name)
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=spec.model,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
            api_key=settings.anthropic_api_key,
        )

    if spec.provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set (needed for '%s')." % name)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=spec.model,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
            api_key=settings.openai_api_key,
        )

    raise ValueError(f"Unsupported provider: {spec.provider}")


# Turn tracing on at import time so every track is observable by default.
from lab.observability.tracing import setup_tracing  # noqa: E402

setup_tracing(settings)
