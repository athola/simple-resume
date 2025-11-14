# =============================================================================
# Simple Resume Makefile
# =============================================================================
# Advanced Makefile with pattern rules, automatic variables, and deduplication
# =============================================================================

# =============================================================================
# CONFIGURATION VARIABLES
# =============================================================================

# Project metadata
PROJECT_NAME := simple-resume
PROJECT_MODULE := simple_resume
PYTHON_VERSION := 3.9

# Paths (all configurable)
SRC_DIR := src
SAMPLE_DIR := sample
OUTPUT_DIR := $(SAMPLE_DIR)/output
ASSETS_DIR := assets
PREVIEW_IMG := $(ASSETS_DIR)/preview.jpg
PREVIEW_PNG := $(ASSETS_DIR)/preview.png

# Commands (all configurable)
UV_CMD := uv
PYTHON_CMD := python3

# uv cache location (avoid read-only $HOME)
UV_CACHE_DIR ?= $(abspath ./.uv-cache)
export UV_CACHE_DIR

PRE_COMMIT_HOME ?= $(abspath ./.pre-commit-cache)
export PRE_COMMIT_HOME

export VIRTUALENV_SUPPRESS_APP_DATA=1
export VIRTUALENV_HOME:=$(PRE_COMMIT_HOME)/venvs
export VIRTUALENV_APP_DATA:=$(PRE_COMMIT_HOME)/app-data
export NPM_CONFIG_CACHE:=$(abspath ./.npm-cache)

# Tool commands with fallbacks
OPEN_CMD := $(shell command -v xdg-open 2>/dev/null || echo wslview)
ifeq ($(OPEN_CMD),wslview)
OPEN_CMD := $(shell command -v wslview 2>/dev/null || echo open)
endif
ifeq ($(OPEN_CMD),open)
OPEN_CMD := $(shell command -v open 2>/dev/null || echo echo)
endif

# Development tools
LINTER := ruff
FORMATTER := ruff
TYPECHECKERS := mypy ty
TEST_RUNNER := pytest
SECURITY_TOOL := bandit

# Common options
FORMATS := pdf html
DEFAULT_FORMAT := pdf
QUALITY := 85
RESIZE := 1200x

# Colors for output
BOLD := \033[1m
GREEN := \033[32m
BLUE := \033[34m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# =============================================================================
# HELPER FUNCTIONS AND MACROS
# =============================================================================

# Function to check if command exists
define check_command
$(shell command -v $(1) >/dev/null 2>&1 && echo "exists" || echo "missing")
endef

# Function to open file with cross-platform support
define open_file
@if command -v xdg-open >/dev/null 2>&1; then \
	xdg-open "$(1)" 2>/dev/null || true; \
elif command -v wslview >/dev/null 2>&1; then \
	wslview "$(1)" 2>/dev/null || true; \
elif command -v open >/dev/null 2>&1; then \
	open "$(1)" 2>/dev/null || true; \
else \
	echo "Please open $(1) manually"; \
fi
endef

# Function to run a type checker with error handling
define run_typechecker
@echo "  Running $(1)..."
@$(UV_CMD) run $(1) $(2) || (echo "$(RED)$(1) failed$(RESET)" && exit 1)
endef

# =============================================================================
# PHONY TARGETS
# =============================================================================

.PHONY: help install lint format typecheck check-all fix-all clean
.PHONY: generate-pdf generate-pdf-sample view-sample dev-setup ci
.PHONY: test test-coverage validate validate-readme-preview update-preview-image
.PHONY: demo-% demo-palette-random demo-latex clean-cache
.PHONY: check-deps install-deps run-lint run-format run-typecheck run-security

# =============================================================================
# HELP AND INFORMATION
# =============================================================================

help: ## Show this help message
	@echo "$(BOLD)$(PROJECT_NAME) - Resume Generation Tool$(RESET)"
	@echo ""
	@echo "$(BLUE)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# =============================================================================
# DEPENDENCY MANAGEMENT
# =============================================================================

check-deps:
	@echo "$(BLUE)Checking dependencies...$(RESET)"
	@$(UV_CMD) --version >/dev/null 2>&1 || (echo "$(RED)uv not found$(RESET)" && exit 1)

install-deps: check-deps ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	@mkdir -p $(UV_CACHE_DIR)
	$(UV_CMD) sync --extra utils --group dev
	@echo "$(GREEN)[OK] Dependencies installed$(RESET)"

install: install-deps ## Install all dependencies including dev tools
	@echo ""
	@echo "$(BLUE)You can now run:$(RESET)"
	@echo "  $(GREEN)make typecheck$(RESET)    # Run type checking"
	@echo "  $(GREEN)make lint$(RESET)         # Run linting"
	@echo "  $(GREEN)make check-all$(RESET)    # Run lint/format/type/security"
	@echo "  $(GREEN)make validate$(RESET)     # Validate README preview & artifacts"

# =============================================================================
# CODE QUALITY TOOLS
# =============================================================================

run-lint: ## Run linting checks
	@echo "$(BLUE)Running linting...$(RESET)"
	$(UV_CMD) run $(LINTER) check .

run-format: ## Run code formatting
	@echo "$(BLUE)Formatting code...$(RESET)"
	$(UV_CMD) run $(FORMATTER) format .

run-typecheck: ## Run all type checkers
	@echo "$(BLUE)Running type checkers...$(RESET)"
	$(call run_typechecker,mypy,.)
	$(call run_typechecker,ty,check .)

run-security: ## Run security analysis
	@echo "$(BLUE)Running security analysis...$(RESET)"
	$(UV_CMD) run $(SECURITY_TOOL) -r $(SRC_DIR) tests -x .venv,.uv-cache,.git -s B101,B404,B603

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

lint: run-lint ## Run linting with ruff

format: run-format ## Format code with ruff

typecheck: run-typecheck ## Run type checking with multiple tools

check-all: install-deps lint format typecheck run-security ## Run all checks

fix-all: format ## Format code and fix auto-fixable issues
	$(UV_CMD) run $(LINTER) check --fix .

test: ## Run all tests
	$(UV_CMD) run $(TEST_RUNNER)

test-coverage: ## Run tests with coverage report
	$(UV_CMD) run $(TEST_RUNNER) --cov=$(SRC_DIR)/$(PROJECT_NAME) --cov-report=term-missing

# =============================================================================
# GENERATION TARGETS
# =============================================================================

# Pattern rule for PDF generation
$(OUTPUT_DIR)/%.pdf: $(SAMPLE_DIR)/input/%.yaml
	@echo "$(BLUE)Generating $(notdir $@)...$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate $(basename $(notdir $<)) --format pdf --data-dir $(SAMPLE_DIR)

# Pattern rule for demo generation with multiple formats
$(OUTPUT_DIR)/demo-%.pdf $(OUTPUT_DIR)/demo-%.html: $(SAMPLE_DIR)/input/%.yaml
	@echo "$(BLUE)Generating demo: $(basename $(notdir $<))$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate $(basename $(notdir $<)) --formats $(FORMATS) --data-dir $(SAMPLE_DIR)

generate-pdf: ## Generate PDF for all Resume files (uses default config directory)
	$(UV_CMD) run $(PROJECT_NAME) generate --format $(DEFAULT_FORMAT)

generate-pdf-sample: ## Generate PDF for all Resume files in sample directory
	$(UV_CMD) run $(PROJECT_NAME) generate --format $(DEFAULT_FORMAT) --data-dir $(SAMPLE_DIR)

# =============================================================================
# DEMO TARGETS (USING PATTERN RULES)
# =============================================================================

# Generic demo pattern
demo-%: ## Generate and preview demo resume (pattern: demo-<name>)
	@echo "$(BLUE)Generating $(subst demo-,,$@) demo...$(RESET)"
	$(eval DEMO_NAME := $(subst demo-,,$@))
	$(eval INPUT_FILE := $(SAMPLE_DIR)/input/$(DEMO_NAME).yaml)
	$(eval OUTPUT_PDF := $(OUTPUT_DIR)/$(DEMO_NAME).pdf)
	@if [ ! -f "$(INPUT_FILE)" ]; then \
		echo "$(RED)Input file not found: $(INPUT_FILE)$(RESET)"; \
		exit 1; \
	fi
	$(UV_CMD) run $(PROJECT_NAME) generate $(DEMO_NAME) --formats $(FORMATS) --data-dir $(SAMPLE_DIR)
	@echo "$(GREEN)[OK] Demo generated: $(OUTPUT_PDF)$(RESET)"
	$(call open_file,$(OUTPUT_PDF))

# Specific demo targets for backward compatibility
demo-palette: ## Generate and preview the palette demo resume
	@echo "$(BLUE)Generating palette demo...$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate sample_palette_demo --formats $(FORMATS) --data-dir $(SAMPLE_DIR)
	@echo "$(GREEN)[OK] Palette demo generated: $(OUTPUT_DIR)/sample_palette_demo.pdf$(RESET)"
	$(call open_file,$(OUTPUT_DIR)/sample_palette_demo.pdf)

demo-multipage: ## Generate and preview the multipage demo resume
	@echo "$(BLUE)Generating multipage demo...$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate sample_multipage_demo --formats $(FORMATS) --data-dir $(SAMPLE_DIR)
	@echo "$(GREEN)[OK] Multipage demo generated: $(OUTPUT_DIR)/sample_multipage_demo.pdf$(RESET)"
	$(call open_file,$(OUTPUT_DIR)/sample_multipage_demo.pdf)

demo-latex: ## Generate and preview the LaTeX-only sample resume
	@echo "$(BLUE)Generating LaTeX demo (no icons/colors)...$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate sample_latex --data-dir $(SAMPLE_DIR) --format $(DEFAULT_FORMAT)
	@echo "$(GREEN)[OK] LaTeX demo generated: $(OUTPUT_DIR)/sample_latex.pdf$(RESET)"
	$(call open_file,$(OUTPUT_DIR)/sample_latex.pdf)

demo-palette-random: ## Generate and preview a randomized palette demo resume
	@echo "$(BLUE)Generating randomized palette demo...$(RESET)"
	$(UV_CMD) run generate-random-palette-demo --output $(SAMPLE_DIR)/input/sample_palette_demo_random.yaml --template $(SAMPLE_DIR)/input/sample_palette_demo.yaml
	$(UV_CMD) run $(PROJECT_NAME) generate --format $(DEFAULT_FORMAT) --data-dir $(SAMPLE_DIR)
	@echo "$(GREEN)[OK] Random palette demo generated: $(OUTPUT_DIR)/sample_palette_demo_random.pdf$(RESET)"
	$(call open_file,$(OUTPUT_DIR)/sample_palette_demo_random.pdf)

view-sample: generate-pdf-sample ## Generate and view sample PDF output
	@echo "$(BOLD)Sample Resume PDFs Generated$(RESET)"
	@echo ""
	@echo "$(BLUE)Generated files:$(RESET)"
	@ls -1h $(OUTPUT_DIR)/*.pdf 2>/dev/null || echo "No PDFs found"
	@echo ""
	@if [ -f "$(OUTPUT_DIR)/sample_1.pdf" ]; then \
		$(call open_file,$(OUTPUT_DIR)/sample_1.pdf); \
	fi

# =============================================================================
# PREVIEW AND VALIDATION
# =============================================================================

check-preview-prereqs:
	@echo "$(BLUE)Checking prerequisites...$(RESET)"
	@if command -v pdftoppm >/dev/null 2>&1; then \
		echo "$(GREEN)[OK] pdftoppm found$(RESET)"; \
	else \
		echo "$(RED)Error: pdftoppm is required$(RESET)"; \
		echo "Install poppler-utils:"; \
		echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"; \
		echo "  macOS: brew install poppler"; \
		exit 1; \
	fi

update-preview-image: check-preview-prereqs ## Update README preview image with latest palette demo
	@echo "$(BLUE)Updating preview image...$(RESET)"
	$(UV_CMD) run $(PROJECT_NAME) generate --format $(DEFAULT_FORMAT) --data-dir $(SAMPLE_DIR)
	@echo "$(BLUE)Extracting first page as image...$(RESET)"
	@pdftoppm -png -f 1 -l 1 $(OUTPUT_DIR)/sample_palette_demo.pdf $(ASSETS_DIR)/preview_new
	@mv $(ASSETS_DIR)/preview_new-1.png $(ASSETS_DIR)/preview_temp.png
	@echo "$(BLUE)Optimizing image...$(RESET)"
	@if command -v convert >/dev/null 2>&1; then \
		echo "$(GREEN)Using ImageMagick for optimization...$(RESET)"; \
		convert $(ASSETS_DIR)/preview_temp.png -quality $(QUALITY) -resize $(RESIZE) $(PREVIEW_IMG); \
		rm -f $(ASSETS_DIR)/preview_temp.png; \
	else \
		echo "$(YELLOW)ImageMagick not available. Using PNG directly.$(RESET)"; \
		mv $(ASSETS_DIR)/preview_temp.png $(PREVIEW_PNG); \
		sed -i 's/preview\.jpg/preview.png/g' README.md; \
	fi
	@echo "$(GREEN)[OK] Preview image updated$(RESET)"

validate-readme-preview: ## Validate that README preview is up-to-date
	@echo "$(BLUE)Checking preview image status...$(RESET)"
	@set -- \
		$(SRC_DIR)/$(PROJECT_NAME)/templates/*.html \
		$(SRC_DIR)/$(PROJECT_NAME)/*.py \
		$(SRC_DIR)/$(PROJECT_NAME)/core/*.py; \
	files_changed=false; \
	preview_file=""; \
	needs_update=false; \
	if [ -f "$(PREVIEW_IMG)" ]; then \
		preview_file="$(PREVIEW_IMG)"; \
	elif [ -f "$(PREVIEW_PNG)" ]; then \
		preview_file="$(PREVIEW_PNG)"; \
	fi; \
	if [ -z "$$preview_file" ]; then \
		echo "$(YELLOW)No preview image found$(RESET)"; \
		needs_update=true; \
	else \
		preview_time=$$(stat -c %Y "$$preview_file" 2>/dev/null || stat -f %m "$$preview_file" 2>/dev/null || echo 0); \
		for file in "$$@"; do \
			if [ -f "$$file" ]; then \
				file_time=$$(stat -c %Y "$$file" 2>/dev/null || stat -f %m "$$file" 2>/dev/null || echo 0); \
				if [ $$file_time -gt $$preview_time ]; then \
					echo "$(YELLOW)  $$file (newer than preview)$(RESET)"; \
					files_changed=true; \
				fi; \
			fi; \
		done; \
		if [ "$$files_changed" = true ]; then \
			needs_update=true; \
			echo "$(YELLOW)Resume files modified since preview update$(RESET)"; \
		fi; \
	fi; \
	if [ "$$needs_update" = true ]; then \
		echo "$(BLUE)Updating preview image...$(RESET)"; \
		$(MAKE) update-preview-image; \
		echo "$(GREEN)[OK] Preview image updated$(RESET)"; \
	else \
		echo "$(GREEN)[OK] Preview image is up-to-date$(RESET)"; \
	fi

validate: validate-readme-preview ## Validate current commit is ready for PR
	@echo "$(BOLD)========================================$(RESET)"
	@echo "$(BLUE)Validating commit is ready for PR...$(RESET)"
	@echo "$(BOLD)========================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)[1/7] Installing dependencies...$(RESET)"
	@mkdir -p $(UV_CACHE_DIR)
	$(UV_CMD) sync --extra utils --group dev
	@echo ""
	@echo "$(YELLOW)[2/7] Running tests...$(RESET)"
	$(UV_CMD) run $(TEST_RUNNER) || (echo "$(RED)Tests failed$(RESET)" && exit 1)
	@echo "$(GREEN)[OK] Tests passed$(RESET)"
	@echo ""
	@echo "$(YELLOW)[3/7] Running linting...$(RESET)"
	$(UV_CMD) run $(LINTER) check . || (echo "$(RED)Linting failed$(RESET)" && exit 1)
	$(UV_CMD) run $(FORMATTER) format --check . || (echo "$(RED)Formatting issues$(RESET)" && exit 1)
	@echo "$(GREEN)[OK] Linting passed$(RESET)"
	@echo ""
	@echo "$(YELLOW)[4/7] Running type checking...$(RESET)"
	$(call run_typechecker,mypy,. --strict)
	$(call run_typechecker,ty,check . --ignore invalid-assignment --ignore invalid-return-type --ignore no-matching-overload)
	@echo "$(GREEN)[OK] Type checking passed$(RESET)"
	@echo ""
	@echo "$(YELLOW)[5/7] Running security analysis...$(RESET)"
	$(UV_CMD) run $(SECURITY_TOOL) -r $(SRC_DIR) tests -x .venv,.uv-cache,.git -s B101,B404,B603 || (echo "$(RED)Security check failed$(RESET)" && exit 1)
	@echo "$(GREEN)[OK] Security analysis passed$(RESET)"
	@echo ""
	@echo "$(YELLOW)[6/7] Running pre-commit hooks...$(RESET)"
	@mkdir -p $(PRE_COMMIT_HOME)
	$(UV_CMD) run pre-commit run --all-files --show-diff-on-failure || (echo "$(RED)Pre-commit failed$(RESET)" && exit 1)
	@echo "$(GREEN)[OK] Pre-commit hooks passed$(RESET)"
	@echo ""
	@echo "$(YELLOW)[7/7] Validating development environment...$(RESET)"
	$(UV_CMD) run python -c "import $(PROJECT_MODULE).utilities; print('  [OK] $(PROJECT_MODULE).utilities imports correctly')"
	$(UV_CMD) run python -c "from $(PROJECT_MODULE).utilities import get_content; print('  [OK] get_content imports correctly')"
	@echo "$(GREEN)[OK] Development environment validated$(RESET)"
	@echo ""
	@echo "$(BOLD)========================================$(RESET)"
	@echo "$(GREEN)ALL CHECKS PASSED!$(RESET)"
	@echo "$(GREEN)Your commit is ready for PR$(RESET)"
	@echo "$(BOLD)========================================$(RESET)"

# =============================================================================
# CLEANUP TARGETS
# =============================================================================

clean-cache: ## Clean cache files only
	@echo "$(BLUE)Cleaning cache files...$(RESET)"
	rm -rf .uv-cache
	rm -rf __pycache__
	rm -rf $(SRC_DIR)/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[OK] Cache cleaned$(RESET)"

clean: clean-cache ## Clean up all generated files and caches
	@echo "$(BLUE)Cleaning all generated files...$(RESET)"
	rm -rf .venv
	rm -rf $(OUTPUT_DIR)
	@echo "$(GREEN)[OK] All files cleaned$(RESET)"

# =============================================================================
# WORKFLOW TARGETS
# =============================================================================

dev-setup: install ## Set up development environment
	@echo "$(GREEN)[OK] Development environment setup complete!$(RESET)"

ci: install check-all ## Run CI checks
	@echo "$(GREEN)[OK] CI checks completed successfully!$(RESET)"

# =============================================================================
# DEBUG AND UTILITIES
# =============================================================================

show-config: ## Show current configuration
	@echo "$(BOLD)Configuration:$(RESET)"
	@echo "  Project: $(PROJECT_NAME)"
	@echo "  Source Dir: $(SRC_DIR)"
	@echo "  Sample Dir: $(SAMPLE_DIR)"
	@echo "  Output Dir: $(OUTPUT_DIR)"
	@echo "  Formats: $(FORMATS)"
	@echo "  Open Command: $(OPEN_CMD)"
	@echo ""
	@echo "$(BOLD)Tools:$(RESET)"
	@echo "  UV: $(shell $(UV_CMD) --version 2>/dev/null || echo 'not found')"
	@echo "  Python: $(shell $(PYTHON_CMD) --version 2>/dev/null || echo 'not found')"
	@echo "  Ruff: $(shell $(UV_CMD) run ruff --version 2>/dev/null || echo 'not found')"
	@echo "  MyPy: $(shell $(UV_CMD) run mypy --version 2>/dev/null || echo 'not found')"
