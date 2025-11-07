.PHONY: help install lint format typecheck check-all fix-all clean generate-pdf generate-pdf-sample view-sample dev-setup ci test test-coverage validate validate-readme-preview update-preview-image

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
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

typecheck: ## Run type checking with mypy and ty
	@echo "Running mypy type checking..."
	@uv run mypy . || (echo "mypy not found. Run 'make install' first." && exit 1)
	@echo ""
	@echo "Running ty type checking..."
	@uv run ty check . || (echo "ty not found. Run 'make install' first." && exit 1)

check-all: lint typecheck ## Run all checks (lint and typecheck)

fix-all: format ## Format code and fix auto-fixable issues
	uv run ruff check --fix .

clean: ## Clean up cache and build files
	rm -rf .venv
	rm -rf .uv-cache
	rm -rf __pycache__
	rm -rf src/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

generate-pdf: ## Generate PDF for all Resume files (uses default config directory)
	uv run simple-resume generate --format pdf

generate-pdf-sample: ## Generate PDF for all Resume files in sample directory
	uv run simple-resume generate --format pdf --data-dir sample

view-sample: generate-pdf-sample ## Generate and view sample PDF output
	@echo "=========================================="
	@echo "Sample Resume PDFs Generated"
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
	@if command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		xdg-open sample/output/sample_1.pdf 2>/dev/null || true; \
	elif command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		wslview sample/output/sample_1.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_1.pdf..."; \
		open sample/output/sample_1.pdf 2>/dev/null || true; \
	else \
		echo "Please open sample/output/sample_1.pdf manually"; \
	fi

demo-palette: ## Generate and preview the palette demo resume (sample_palette_demo.yaml)
	@echo "Generating palette demo resume..."
	uv run simple-resume generate --formats pdf html --data-dir sample
	@echo ""
	@echo "Palette demo generated at sample/output/sample_palette_demo.pdf"
	@echo "Additional HTML previews saved under sample/output/*.html"
	@echo "This resume uses the YAML config.palette block to control colors."
	@echo ""
	@if command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo.pdf..."; \
		xdg-open sample/output/sample_palette_demo.pdf 2>/dev/null || true; \
	elif command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo.pdf..."; \
		wslview sample/output/sample_palette_demo.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo.pdf..."; \
		open sample/output/sample_palette_demo.pdf 2>/dev/null || true; \
	else \
		echo "Open sample/output/sample_palette_demo.pdf manually to view the palette demo."; \
	fi

demo-multipage: ## Generate and preview the multipage demo resume (sample_multipage_demo.yaml)
	@echo "Generating multipage demo resume..."
	uv run simple-resume generate sample_multipage_demo --formats pdf html --data-dir sample
	@echo ""
	@echo "Multipage demo generated at sample/output/sample_multipage_demo.pdf"
	@echo "Additional HTML preview saved under sample/output/sample_multipage_demo.html"
	@echo "This resume intentionally spans two pages to showcase overflow handling."
	@echo ""
	@if command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_multipage_demo.pdf..."; \
		xdg-open sample/output/sample_multipage_demo.pdf 2>/dev/null || true; \
	elif command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_multipage_demo.pdf..."; \
		wslview sample/output/sample_multipage_demo.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_multipage_demo.pdf..."; \
		open sample/output/sample_multipage_demo.pdf 2>/dev/null || true; \
	else \
		echo "Open sample/output/sample_multipage_demo.pdf manually to view the multipage demo."; \
	fi

update-preview-image: ## Update README preview image with latest palette demo
	@echo "Checking prerequisites..."
	@if ! command -v pdftoppm >/dev/null 2>&1; then \
		echo "Error: pdftoppm is required but not installed."; \
		echo "Please install poppler-utils package:"; \
		echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"; \
		echo "  macOS: brew install poppler"; \
		echo "  Or install ImageMagick which includes pdftoppm"; \
		exit 1; \
	fi
	@echo "Generating latest palette demo for preview image..."
	@uv run simple-resume generate --format pdf --data-dir sample
	@echo "Extracting first page as image..."
	@pdftoppm -png -f 1 -l 1 sample/output/sample_palette_demo.pdf assets/preview_new
	@mv assets/preview_new-1.png assets/preview_temp.png
	@echo "Optimizing image..."
	@if command -v convert >/dev/null 2>&1; then \
		echo "Using ImageMagick for optimization..."; \
		convert assets/preview_temp.png -quality 85 -resize 1200x assets/preview.jpg; \
		rm -f assets/preview_temp.png; \
	else \
		echo "ImageMagick not available. Using direct PNG."; \
		mv assets/preview_temp.png assets/preview.png; \
		sed -i 's/preview\.jpg/preview.png/g' README.md; \
	fi
	@echo "Preview image updated at assets/preview.jpg"
	@echo ""
	@echo "The README.md preview has been updated with the latest resume styling!"

demo-palette-random: ## Generate and preview a randomized palette demo resume
	@echo "Generating randomized palette demo input..."
	uv run generate-random-palette-demo --output sample/input/sample_palette_demo_random.yaml --template sample/input/sample_palette_demo.yaml
	@echo "Rendering randomized palette demo resume..."
	uv run simple-resume generate --format pdf --data-dir sample
	@echo ""
	@echo "Random palette demo generated at sample/output/sample_palette_demo_random.pdf"
	@echo "This resume randomizes both content and palette selection to showcase variety."
	@echo ""
	@if command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo_random.pdf..."; \
		xdg-open sample/output/sample_palette_demo_random.pdf 2>/dev/null || true; \
	elif command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo_random.pdf..."; \
		wslview sample/output/sample_palette_demo_random.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_palette_demo_random.pdf..."; \
		open sample/output/sample_palette_demo_random.pdf 2>/dev/null || true; \
	else \
		echo "Open sample/output/sample_palette_demo_random.pdf manually to view the randomized palette demo."; \
	fi

demo-latex: ## Generate and preview the LaTeX-only sample resume (sample_latex.yaml)
	@echo "Generating LaTeX demo resume (no icons/colors)..."
	uv run simple-resume generate sample_latex --data-dir sample --format pdf
	@echo ""
	@echo "LaTeX demo generated at sample/output/sample_latex.pdf"
	@echo "This resume uses config.output_mode: latex and renders via the TeX backend."
	@echo ""
	@if command -v xdg-open >/dev/null 2>&1; then \
		echo "Opening sample_latex.pdf..."; \
		xdg-open sample/output/sample_latex.pdf 2>/dev/null || true; \
	elif command -v wslview >/dev/null 2>&1; then \
		echo "Opening sample_latex.pdf..."; \
		wslview sample/output/sample_latex.pdf 2>/dev/null || true; \
	elif command -v open >/dev/null 2>&1; then \
		echo "Opening sample_latex.pdf..."; \
		open sample/output/sample_latex.pdf 2>/dev/null || true; \
	else \
		echo "Open sample/output/sample_latex.pdf manually to view the LaTeX demo."; \
	fi

dev-setup: install ## Set up development environment
	@echo "Development environment setup complete!"

ci: install check-all ## Run CI checks

test: ## Run all tests
	uv run pytest

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src/simple_resume --cov-report=term-missing

validate: validate-readme-preview ## Validate current commit is ready for PR (runs ALL workflow checks)
	@echo "=========================================="
	@echo "Validating commit is ready for PR..."
	@echo "Running ALL CI workflow checks locally"
	@echo "=========================================="
	@echo ""
	@echo "[1/8] Installing dependencies..."
	uv sync --extra utils --group dev
	@echo ""
	@echo "[2/7] Running tests..."
	uv run pytest || (echo "Tests failed - fix before pushing" && exit 1)
	@echo "Tests passed"
	@echo ""
	@echo "[3/7] Running linting checks..."
	uv run ruff check . || (echo "Ruff linting failed - run 'make fix-all' to auto-fix" && exit 1)
	uv run ruff format --check . || (echo "Code formatting issues - run 'make fix-all'" && exit 1)
	@echo "Linting passed"
	@echo ""
	@echo "[4/7] Running type checking..."
	@echo "  - MyPy (strict mode)..."
	uv run mypy . --strict || (echo "MyPy type checking failed" && exit 1)
	@echo "  - Ty..."
	uv run ty check . --ignore invalid-assignment --ignore invalid-return-type --ignore no-matching-overload || (echo "Ty type checking failed" && exit 1)
	@echo "  - Pyright..."
	npx --yes pyright . || (echo "Pyright type checking failed" && exit 1)
	@echo "  - Pytype..."
	uv run pytype . || (echo "Pytype type checking failed" && exit 1)
	@echo "All type checkers passed"
	@echo ""
	@echo "[5/7] Running security analysis..."
	uv run bandit -r src/simple_resume tests -x .venv,.uv-cache,.git -s B101,B404,B603 || (echo "Bandit security check failed" && exit 1)
	@echo "Security analysis passed"
	@echo ""
	@echo "[6/7] Running pre-commit hooks on all files..."
	uv run pre-commit run --all-files --show-diff-on-failure || (echo "Pre-commit hooks failed" && exit 1)
	@echo "Pre-commit hooks passed"
	@echo ""
	@echo "[7/7] Validating development environment..."
	@uv run python -c "import simple_resume.utilities; print('  ✓ simple_resume.utilities imports correctly')"
	@uv run python -c "from simple_resume.utilities import get_content; print('  ✓ get_content imports correctly')"
	@echo "Development environment validated"
	@echo ""
	@echo "=========================================="
	@echo "ALL CHECKS PASSED!"
	@echo "Your commit is ready for PR"
	@echo "=========================================="

validate-readme-preview: ## Validate that README preview is up-to-date with latest changes
	@echo "Checking if resume output files have been modified..."
	@echo ""
	@echo "Checking for changes in files that affect resume output..."
	@set -- \
		src/simple_resume/templates/*.html \
		src/simple_resume/static/css/*.css \
		src/simple_resume/*.py \
		src/simple_resume/core/*.py; \
	files_changed=false; \
	preview_jpg=assets/preview.jpg; \
	preview_png=assets/preview.png; \
	needs_update=false; \
	\
	if [ ! -f $$preview_jpg ] && [ ! -f $$preview_png ]; then \
		echo "No preview image found. Will create one..."; \
		needs_update=true; \
	else \
		preview_file=$$preview_jpg; \
		[ ! -f $$preview_file ] && preview_file=$$preview_png; \
		if [ -f $$preview_file ]; then \
			preview_time=$$(stat -c %Y $$preview_file 2>/dev/null || stat -f %m $$preview_file 2>/dev/null || echo 0); \
			for file in "$$@"; do \
				if [ -f "$$file" ]; then \
					file_time=$$(stat -c %Y "$$file" 2>/dev/null || stat -f %m "$$file" 2>/dev/null || echo 0); \
					if [ $$file_time -gt $$preview_time ]; then \
						echo "  $$file (newer than preview)"; \
						files_changed=true; \
					fi; \
				fi; \
			done; \
			if [ "$$files_changed" = true ]; then \
				needs_update=true; \
				echo "Resume output files modified since last preview update"; \
			fi; \
		fi; \
	fi; \
	\
	if [ "$$needs_update" = true ]; then \
		echo ""; \
		echo "Updating README preview image with latest changes..."; \
		$(MAKE) update-preview-image; \
		echo ""; \
		echo "README preview image updated successfully!"; \
		echo ""; \
		echo "Tip: Review the updated preview before committing:"; \
		echo "   git add assets/preview.*"; \
		echo "   git commit -m \"Update README preview with latest resume styling\""; \
	else \
		echo "README preview image is up-to-date"; \
		echo "   No changes detected in resume output files"; \
	fi
