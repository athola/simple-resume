# GitHub Actions Workflows

This document explains the GitHub Actions workflows used for code quality, testing, and CI/CD in the CV project.

## Overview

The project uses multiple GitHub Actions workflows to ensure code quality, security, and reliability:

- **Test Suite** (`test.yml`) - Main testing workflow
- **Linting** (`lint.yml`) - Dedicated code linting
- **Type Checking** (`typecheck.yml`) - Comprehensive type analysis
- **Code Quality** (`code-quality.yml`) - Advanced quality checks
- **Pre-commit** (`pre-commit.yml`) - Pre-commit hook validation

## Test Suite (test.yml)

**Triggers**: Push to main, Pull Requests to main

### Jobs:
- **test**: Main test job
  - Sets up Python 3.10
  - Installs dependencies with uv
  - Runs pytest test suite
  - Runs mypy type checking
  - Runs ty type checking
  - Runs ruff linting

```bash
uv run pytest
uv run mypy src/cv/
uv run ty check src/cv/
uv run ruff check src/cv/
```

## Linting (lint.yml)

**Triggers**: Push to main, Pull Requests to main

### Jobs:
- **ruff**: Ruff linting and formatting
  - Checks code style and formatting
  - Uses ruff check and ruff format

- **flake8**: Additional linting
  - Traditional Python linting with line length limits
  - Configured for 100-character line length

- **pylint**: Static analysis
  - Comprehensive code quality analysis
  - Generates quality scores

## Type Checking (typecheck.yml)

**Triggers**: Push to main, Pull Requests to main

### Jobs:
- **mypy**: Static type checking
  - Strict type checking with mypy
  - Comprehensive type validation

- **ty**: Fast type checking
  - Ultra-fast type checker for quick feedback
  - Complements mypy with different analysis approach

- **pyright**: Microsoft's type checker
  - Alternative type checking perspective
  - Provides additional type insights

- **pytype**: Google's type checker
  - Statistical type inference
  - Helps catch subtle type issues

## Code Quality (code-quality.yml)

**Triggers**: Push to main, Pull Requests to main

### Jobs:
- **code-quality**: Comprehensive quality checks
  - Combines ruff, mypy, ty, flake8, and pylint
  - Single job for quick feedback on all tools

- **security**: Security analysis
  - **Bandit**: Security vulnerability scanner
  - **Safety**: Dependency security checker
  - Uploads security reports as artifacts

- **complexity**: Code complexity analysis
  - **Radon**: Cyclomatic complexity analysis
  - **Xenon**: Complexity monitoring
  - Uploads complexity reports as artifacts

- **documentation**: Documentation quality
  - Docstring coverage analysis
  - README link validation
  - Markdown file validation

## Pre-commit (pre-commit.yml)

**Triggers**: Push to main, Pull Requests to main

### Jobs:
- **pre-commit**: Pre-commit hook validation
  - Runs all pre-commit hooks on all files
  - Caches pre-commit dependencies for speed
  - Shows diff on failure

- **local-dev-setup**: Local development validation
  - Tests make commands (if Makefile exists)
  - Validates direct uv commands
  - Validates development environment setup

## Pre-commit Configuration

The project uses `.pre-commit-config.yaml` with the following hooks:

### Linting and Formatting:
- **Ruff**: Fast Python linting and formatting
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Additional linting
- **pylint**: Static analysis

### Type Checking:
- **mypy**: Static type checking
- **ty**: Fast type checking

### Security:
- **bandit**: Security vulnerability scanning

### Documentation:
- **blacken-docs**: Markdown formatting
- **markdownlint-cli2**: Markdown linting

### Quality:
- **pytest-check**: Test collection validation

## Local Development

### Setting up pre-commit hooks:

```bash
# Install dependencies
uv sync --extra utils

# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Manual quality checks:

```bash
# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/cv/ --strict
uv run ty check src/cv/

# Additional linting
uv run flake8 src/ tests/ --max-line-length=100
uv run pylint src/cv/

# Testing
uv run pytest

# Security
pip install bandit safety
bandit -r src/
safety check

# Complexity
pip install radon xenon
radon cc src/cv/
xenon --max-absolute B src/cv/
```

## Workflow Configuration

### Python Version
- **Target**: Python 3.10
- **Reason**: Compatibility with Ubuntu 22.04 LTS

### Package Management
- **Tool**: uv (modern Python package installer)
- **Benefits**: Fast, reliable, and feature-rich

### Caching
- **Pre-commit**: Cached for faster runs
- **Dependencies**: uv handles dependency caching

### Artifacts
- **Security reports**: Uploaded from security scans
- **Complexity reports**: Uploaded from analysis
- **Test coverage**: Generated and uploaded by pytest

## Best Practices

### Workflow Design:
1. **Fast feedback**: Critical checks run first
2. **Parallel execution**: Independent jobs run in parallel
3. **Fail fast**: Workflows stop on first failure
4. **Artifact retention**: Important reports saved for debugging

### Tool Configuration:
1. **Consistent settings**: All tools use 100-character line length
2. **Strict mode**: Type checking uses strict settings
3. **Comprehensive coverage**: Multiple tools provide different perspectives

### Performance:
1. **Caching**: Pre-commit and dependencies cached
2. **Parallel execution**: Jobs run independently when possible
3. **Fast tools**: Preference given to fast tools (ruff, ty)

## Troubleshooting

### Common Issues:
1. **Pre-commit failures**: Run `pre-commit run --all-files` locally
2. **Type errors**: Check mypy and ty output for specific issues
3. **Linting failures**: Review ruff/flake8 output and fix formatting
4. **Security issues**: Review bandit/safety reports and address vulnerabilities

### Getting Help:
- Check workflow logs in GitHub Actions
- Run commands locally to reproduce issues
- Review tool documentation for configuration options
- Use `--help` flags for tool-specific guidance

This comprehensive workflow setup ensures high code quality, security, and maintainability for the CV project.
