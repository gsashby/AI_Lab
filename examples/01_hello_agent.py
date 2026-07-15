"""Phase 0 deliverable: a traced hello-world agent.

Run it:
    python examples/01_hello_agent.py
    python examples/01_hello_agent.py --model openai-default "Explain MCP in one sentence."

What it demonstrates:
  * The MODEL_REGISTRY: pick a provider by stable name (Anthropic is default).
  * Tracing-by-default: importing `lab` turns LangSmith on. If a key is set,
    this run shows up in your LangSmith project; if not, it still runs and warns.

This is deliberately the *simplest* possible agent (one model call). Track 1
adds tools, memory, and structured output on top of exactly this pattern.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running directly (`python examples/01_hello_agent.py`) without installing,
# by putting the repo root on the path. If you `pip install -e .`, this is a no-op.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Importing lab.config bootstraps settings + tracing as a side effect.
from lab.config import get_model, settings
from lab.observability.tracing import tracing_active, traceable


@traceable(name="hello_agent")
def run(prompt: str, model_name: str | None = None) -> str:
    """Send a single prompt to a registry model and return the text reply."""
    model = get_model(model_name)  # None -> settings.lab_default_model
    response = model.invoke(prompt)
    # LangChain chat models return a message; `.content` is the text.
    return response.content if hasattr(response, "content") else str(response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Traced hello-world agent.")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Say hello and tell me one interesting fact about AI agents.",
        help="The prompt to send.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Registry name (e.g. anthropic-default, openai-default). "
        f"Default: {settings.lab_default_model}",
    )
    args = parser.parse_args(argv)

    print(f"[model] {args.model or settings.lab_default_model}")
    print(f"[tracing] {'on -> project ' + settings.langsmith_project if tracing_active() else 'off'}")
    print("-" * 60)

    try:
        reply = run(args.prompt, args.model)
    except Exception as exc:  # keep the learning loop friendly
        print(f"Error: {exc}", file=sys.stderr)
        print(
            "\nTip: copy .env.example to .env and set the relevant API key.",
            file=sys.stderr,
        )
        return 1

    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
