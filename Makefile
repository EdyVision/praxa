# Praxa — local development targets
#
#   make help
#   make install
#   make test
#   make test.coverage
#   make format

.DEFAULT_GOAL := help

UV ?= uv
PYTEST ?= $(UV) run pytest
COVERAGE ?= $(UV) run coverage
BLACK ?= $(UV) run black

SRC := src/praxa
TESTS := tests
EXAMPLES := examples

.PHONY: help install install.dev test test.coverage coverage.check validate format format.check clean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9._-]+:.*?##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: install.dev ## Install package + dev tools into .venv

install.dev: ## Sync editable install with [dev] extras (pytest, coverage, black)
	$(UV) sync --extra dev
	@echo "Ready. Activate with: source .venv/bin/activate"

test: ## Run tests
	$(PYTEST) $(TESTS) -q

test.coverage: ## Run tests with coverage report (+ XML)
	$(COVERAGE) run -m pytest $(TESTS) -q
	$(COVERAGE) report -m
	$(COVERAGE) xml -o coverage.xml
	@echo "HTML (optional): $(COVERAGE) html && open htmlcov/index.html"

coverage.check: ## Run tests and fail if coverage < 85%
	$(UV) run python scripts/validate_coverage.py

validate: ## Smoke-validate library paths (FakeBackend, no network)
	$(UV) run python scripts/validate_smoke.py

format: ## Format with black
	$(BLACK) $(SRC) $(TESTS) $(EXAMPLES) scripts

format.check: ## Check formatting without writing
	$(BLACK) --check $(SRC) $(TESTS) $(EXAMPLES) scripts

clean: ## Remove caches and coverage artifacts
	rm -rf .pytest_cache .coverage coverage.xml htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true
