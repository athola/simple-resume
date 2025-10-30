# GitHub Actions Workflows

We use GitHub Actions to automate code quality checks on every push and pull
request to `main`. This guide explains what each workflow does and how to run
the checks locally.

## CI/CD Workflows

- **`test.yml`**: Runs the `pytest` suite and performs static analysis with
  `mypy`, `ty`, and `ruff`. This is the main quality gate.
- **`lint.yml`**: Enforces code style and catches common errors using `ruff`,
  `flake8`, and `pylint`.
- **`typecheck.yml`**: Validates type hints using a matrix of checkers:
  `mypy`, `ty`, `pyright`, and `pytype`.
- **`code-quality.yml`**: Scans for security vulnerabilities and cyclomatic
  complexity with `Bandit`, `Safety`, `Radon`, and `Xenon`.
- **`pre-commit.yml`**: Validates the `.pre-commit-config.yaml` file itself.

## Local Development

### Pre-commit Hooks

Hooks run `ruff`, `mypy`, and security checks automatically on every commit.

```bash
pre-commit install                # Install hooks
pre-commit run --all-files        # Run hooks on all files
```

### Manual Execution

To run checks manually:

```bash
# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/easyresume/ --strict
uv run ty check src/easyresume/

# Testing
uv run pytest
```

## Configuration

All workflows use Python 3.10 and `uv`. Security and complexity reports are stored as build artifacts.
