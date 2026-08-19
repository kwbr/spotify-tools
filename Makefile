.DEFAULT_GOAL := help

UV_RUN := uv run --locked

.PHONY: help check lint format-check format typecheck test clean

help: ## Show available development commands
	@awk 'BEGIN {FS = ":.*## "; printf "Available targets:\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: lint format-check typecheck test ## Run all quality checks and tests

lint: ## Run Ruff lint checks
	$(UV_RUN) ruff check .

format-check: ## Verify Ruff formatting without changing files
	$(UV_RUN) ruff format --check .

format: ## Apply Ruff lint fixes and formatting
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

typecheck: ## Run Pyright type checking
	$(UV_RUN) pyright

test: ## Run the test suite
	$(UV_RUN) pytest

clean: ## Remove generated test, lint, and coverage artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find src tests -type d -name "__pycache__" -prune -exec rm -rf {} +
	find src tests -type f -name "*.pyc" -delete
