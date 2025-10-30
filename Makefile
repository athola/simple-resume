.PHONY: help install lint format typecheck check-all fix-all clean generate-pdf generate-pdf-sample view-sample dev-setup ci test test-coverage validate

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
	uv run ruff check src/easyresume/

format: ## Format code with ruff
	uv run ruff format src/easyresume/

typecheck: ## Run type checking with mypy and ty
	@echo "Running mypy type checking..."
	@uv run mypy src/easyresume/ || (echo "mypy not found. Run 'make install' first." && exit 1)
	@echo ""
	@echo "Running ty type checking..."
	@uv run ty check src/easyresume/ || (echo "ty not found. Run 'make install' first." && exit 1)

check-all: lint typecheck ## Run all checks (lint and typecheck)

fix-all: format ## Format code and fix auto-fixable issues
	uv run ruff check --fix src/easyresume/

clean: ## Clean up cache and build files
	rm -rf .venv
	rm -rf .uv-cache
	rm -rf __pycache__
	rm -rf src/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

generate-pdf: ## Generate PDF for all CV files (uses default config directory)
	uv run generate-pdf

generate-pdf-sample: ## Generate PDF for all CV files in sample directory
	uv run generate-pdf --data-dir sample

view-sample: generate-pdf-sample ## Generate and view sample PDF output
	@echo "=========================================="
	@echo "Sample CV PDFs Generated"
	@echo "=========================================="
	@echo ""
	@echo "Generated files:"
	@ls -1h sample/output/*.pdf 2>/dev/null || echo "No PDFs found"
	@echo ""
	@echo "To view the PDFs:"
	@echo "  - Linux: xdg-open sample/output/sample_1.pdf"
	@echo "  - macOS: open sample/output/sample_1.pdf"
	@echo "  - Windows: start sample/output/sample_1.pdf"
	@echo ""
	@if command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		wslview sample/output/sample_1.pdf 2>/dev/null || true; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		xdg-open sample/output/sample_1.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		open sample/output/sample_1.pdf 2>/dev/null || true; \
	else \
		echo "Please open sample/output/sample_1.pdf manually"; \
	fi

dev-setup: install ## Set up development environment
	@echo "Development environment setup complete!"

ci: install check-all ## Run CI checks

test: ## Run all tests
	uv run pytest

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src/easyresume --cov-report=term-missing

validate: ## Validate current commit is ready for PR (runs ALL workflow checks)
	@echo "=========================================="
	@echo "Validating commit is ready for PR..."
	@echo "Running ALL CI workflow checks locally"
	@echo "=========================================="
	@echo ""
	@echo "[1/8] Installing dependencies..."
	uv sync --extra utils --group dev
	@echo ""
	@echo "[2/8] Running tests..."
	uv run pytest || (echo "❌ Tests failed - fix before pushing" && exit 1)
	@echo "✅ Tests passed"
	@echo ""
	@echo "[3/8] Running linting checks..."
	uv run ruff check src/ tests/ || (echo "❌ Ruff linting failed - run 'make fix-all' to auto-fix" && exit 1)
	uv run ruff format --check src/ tests/ || (echo "❌ Code formatting issues - run 'make fix-all'" && exit 1)
	@echo "✅ Linting passed"
	@echo ""
	@echo "[4/8] Running type checking..."
	@echo "  - MyPy (strict mode)..."
	uv run mypy src/easyresume/ --strict || (echo "❌ MyPy type checking failed" && exit 1)
	@echo "  - Ty..."
	uv run ty check src/easyresume/ || (echo "❌ Ty type checking failed" && exit 1)
	@echo "  - Pyright..."
	npx --yes pyright src/easyresume/ || (echo "❌ Pyright type checking failed" && exit 1)
	@echo "  - Pytype..."
	uv run pytype src/easyresume/ || (echo "❌ Pytype type checking failed" && exit 1)
	@echo "✅ All type checkers passed"
	@echo ""
	@echo "[5/8] Running Pylint rules via Ruff..."
	uv run ruff check src/easyresume/ --select=PL || (echo "❌ Ruff Pylint rules failed" && exit 1)
	@echo "✅ Pylint rules passed"
	@echo ""
	@echo "[6/8] Running security analysis..."
	uv run bandit -r src/easyresume/ || (echo "❌ Bandit security check failed" && exit 1)
	@echo "✅ Security analysis passed"
	@echo ""
	@echo "[7/8] Running pre-commit hooks on all files..."
	uv run pre-commit run --all-files --show-diff-on-failure || (echo "❌ Pre-commit hooks failed" && exit 1)
	@echo "✅ Pre-commit hooks passed"
	@echo ""
	@echo "[8/8] Validating development environment..."
	@uv run python -c "import easyresume.utilities; print('  ✓ easyresume.utilities imports correctly')"
	@uv run python -c "from easyresume.utilities import get_content; print('  ✓ get_content imports correctly')"
	@echo "✅ Development environment validated"
	@echo ""
	@echo "=========================================="
	@echo "✅ ALL CHECKS PASSED!"
	@echo "Your commit is ready for PR"
	@echo "=========================================="
