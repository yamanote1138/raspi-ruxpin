.PHONY: help install install-dev install-pi test test-verbose test-cov run dev frontend clean lint format type-check

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies for Mac development (mock GPIO)
	uv venv
	uv pip install -e ".[dev,mock]"
	cd frontend && npm install

install-dev:  ## Install development dependencies with mock GPIO
	uv pip install -e ".[dev,mock]"

install-pi:  ## Install dependencies for Raspberry Pi (hardware)
	uv venv
	uv pip install -e ".[hardware]"

test:  ## Run backend tests
	uv run pytest

test-verbose:  ## Run backend tests with verbose output
	uv run pytest -v

test-cov:  ## Run backend tests with coverage report
	uv run pytest --cov=backend --cov-report=term-missing --cov-report=html

run:  ## Run backend server
	uv run python -m backend.main

dev:  ## Run backend in development mode (auto-reload)
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080

frontend:  ## Run frontend dev server
	cd frontend && npm run dev

clean:  ## Clean build artifacts and caches
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:  ## Run linters (ruff)
	uv run ruff check backend/

format:  ## Format code with ruff
	uv run ruff format backend/

type-check:  ## Run type checker (mypy)
	uv run mypy backend/

check: lint type-check test  ## Run all checks (lint, type-check, test)
