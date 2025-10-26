.PHONY: help install lint format typecheck clean run-server generate-pdf validate

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies including dev tools
	@echo "Installing dependencies with uv..."
	uv sync --extra utils
	@echo "Dependencies installed successfully!"
	@echo ""
	@echo "You can now run:"
	@echo "  make typecheck    # Run type checking"
	@echo "  make lint         # Run linting"
	@echo "  make check-all    # Run all checks"

lint: ## Run linting with ruff
	uv run ruff check src/cv/

format: ## Format code with ruff
	uv run ruff format src/cv/

lint-fix: ## Auto-fix linting issues with ruff
	uv run ruff check --fix src/cv/

typecheck: ## Run type checking with mypy and ty
	@echo "Running mypy type checking..."
	@uv run mypy src/cv/ || (echo "mypy not found. Run 'make install' first." && exit 1)
	@echo ""
	@echo "Running ty type checking..."
	@uv run ty check src/cv/ || (echo "ty not found. Run 'make install' first." && exit 1)

check-all: lint typecheck ## Run all checks (lint and typecheck)

fix-all: format lint-fix ## Format code and fix auto-fixable issues

clean: ## Clean up cache and build files
	rm -rf .venv
	rm -rf .uv-cache
	rm -rf __pycache__
	rm -rf src/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-server: ## Run the Flask development server
	uv run run-server

generate-pdf: ## Generate PDF for all CV files (uses default config directory)
	uv run generate-pdf

generate-pdf-sample: ## Generate PDF for all CV files in sample directory
	uv run generate-pdf --data-dir sample

dev-setup: install ## Set up development environment
	@echo "Development environment setup complete!"

ci: install check-all ## Run CI checks

test: ## Run all tests
	uv run pytest

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src/cv --cov-report=term-missing

validate: ## Validate current commit is ready for PR (runs all workflow checks)
	@echo "Validating commit is ready for PR..."
	@echo ""
	@echo "Installing dependencies..."
	uv sync --extra utils
	@echo ""
	@echo "Running tests..."
	uv run pytest || (echo "Tests failed - fix before pushing" && exit 1)
	@echo ""
	@echo "Running linting checks..."
	uv run ruff check src/ tests/ || (echo "Linting failed - run 'make fix-all' to auto-fix" && exit 1)
	uv run ruff format --check src/ tests/ || (echo "Code formatting issues - run 'make fix-all'" && exit 1)
	@echo ""
	@echo "Running type checking..."
	uv run mypy src/cv/ || (echo "MyPy type checking failed" && exit 1)
	uv run ty check src/cv/ || (echo "Ty type checking failed" && exit 1)
	@echo ""
	@echo "Running additional static analysis with ruff pylint rules..."
	uv run ruff check src/cv/ --select=PL || (echo "Ruff pylint rules failed" && exit 1)
	@echo ""
	@echo "All checks passed! Commit is ready for PR"