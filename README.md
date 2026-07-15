# ai-lab

A personal learning lab for building **agents**, **agentic orchestration** (LangGraph),
**MCP servers**, and an **observability + eval** framework. Python-first.

This repo is built in phases (see `ai-lab-plan.md`). You're looking at **Phase 0 —
Foundation**: packaging, a dual-provider model registry, tracing-on-by-default, and a
runnable traced hello-world agent.

## Quick start

```bash
# 1. Install (uv recommended)
uv sync            # or:  pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
#   edit .env: set ANTHROPIC_API_KEY (default provider) and LANGSMITH_API_KEY

# 3. Confirm setup without making any API calls
make check

# 4. Run the traced hello-world agent
make hello
#   or:  python examples/01_hello_agent.py --model openai-default "Explain MCP briefly."
```

If `LANGSMITH_API_KEY` is set, the run appears in your LangSmith project
(`ai-lab` by default). Without it, the agent still runs and prints a warning —
a learning lab should never be blocked on a tracing account.

## What's here (Phase 0)

```
ai-lab/
├── pyproject.toml            # uv-managed deps; mcp/evals extras staged for later phases
├── .env.example              # provider keys + LangSmith config
├── Makefile                  # install / check / hello / lint
├── lab/
│   ├── config.py             # Settings + MODEL_REGISTRY + get_model(); bootstraps tracing
│   ├── observability/
│   │   └── tracing.py        # LangSmith bootstrap; swappable backend; @traceable re-export
│   ├── agents/               # Track 1  (Phase 1)
│   ├── orchestration/        # Track 2  (Phase 2)
│   └── mcp_servers/          # Track 3  (Phase 3)
└── examples/
    └── 01_hello_agent.py     # the Phase 0 deliverable
```

## The model registry

Ask for a model by a **stable name**, not a provider detail:

```python
from lab.config import get_model
model = get_model()                    # default: anthropic-default
model = get_model("openai-default")    # switch providers in one arg
```

Registered out of the box (edit model ids in `lab/config.py`):

| Name | Provider | Purpose |
|------|----------|---------|
| `anthropic-default` | Anthropic | **default** — main workhorse |
| `anthropic-fast` | Anthropic | cheap/fast for loops & drafts |
| `openai-default` | OpenAI | cross-provider learning & eval matrix |
| `openai-fast` | OpenAI | cheap/fast OpenAI |

This one indirection is what lets orchestration nodes pick different models and
what feeds the model-matrix evals later (Phase 4).

## Tracing is on by default

Importing `lab` calls `setup_tracing()`, which wires LangSmith from your `.env`.
Everything downstream (agents, graphs) is auto-instrumented. To swap to a
self-hosted backend later (Langfuse / Phoenix), change **only** `lab/observability/tracing.py`.

## Next: Phase 1

Add real tools, memory, and structured output on top of `01_hello_agent.py` to
produce `examples/02_agent_with_tools.py`, plus the first golden eval set.
