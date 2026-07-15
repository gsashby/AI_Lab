.PHONY: install hello lint check clean

# Install with uv (falls back to pip if uv is absent).
install:
	uv sync || pip install -e ".[dev]"

# Phase 0 deliverable: a traced hello-world agent.
hello:
	python examples/01_hello_agent.py

# Smoke test: import the package and print the resolved config (no API calls).
check:
	python -c "from lab.config import settings, describe_registry; print(describe_registry())"

lint:
	ruff check lab examples

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .pytest_cache
