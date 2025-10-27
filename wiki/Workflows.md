# GitHub Actions Workflows

This document covers the GitHub Actions workflows used in this project.

## Overview

The following workflows are configured to run on pushes and pull requests to `main`:

- **Test Suite** (`test.yml`)
- **Linting** (`lint.yml`)
- **Type Checking** (`typecheck.yml`)
- **Code Quality** (`code-quality.yml`)
- **Pre-commit** (`pre-commit.yml`)

## Workflows

### Test Suite (`test.yml`)

Runs the full test and linting suite.

- Sets up Python 3.10
- Installs dependencies with `uv`
- Runs `pytest`, `mypy`, `ty`, and `ruff`

### Linting (`lint.yml`)

Runs formatters and linters.

- `ruff` (linting and formatting)
- `flake8`
- `pylint`

### Type Checking (`typecheck.yml`)

Runs a matrix of type checkers.

- `mypy`
- `ty`
- `pyright`
- `pytype`

### Code Quality (`code-quality.yml`)

Runs static analysis and documentation checks.

- **code-quality**: Aggregates reports from other jobs.
- **security**: Runs `Bandit` and `Safety`.
- **complexity**: Runs `Radon` and `Xenon`.
- **documentation**: Checks docstring coverage and Markdown links.

### Pre-commit (`pre-commit.yml`)

Validates `pre-commit` hooks and the local development setup.

- **pre-commit**: Runs all hooks defined in `.pre-commit-config.yaml`.
- **local-dev-setup**: Validates `Makefile` and `uv` commands.

## Local Development

### Pre-commit

To run all hooks automatically on each commit:

```bash
# Install dependencies and pre-commit
uv sync --extra utils
pip install pre-commit

# Install hooks
pre-commit install

# Optional: run on all files
pre-commit run --all-files
```

### Manual Checks

To run tools manually:

```bash
# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/cv/ --strict
uv run ty check src/cv/

# Testing
uv run pytest
```

## Configuration

- **Python**: 3.10 (matches Ubuntu 22.04 LTS)
- **Dependencies**: `uv`
- **Artifacts**: Security and complexity reports are uploaded from their respective jobs.
