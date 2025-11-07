# GitHub Actions Workflows

We use GitHub Actions to automatically check our code for errors, style issues, and
security vulnerabilities. These checks run on every push and pull request to the
`main` branch. This guide explains each workflow and how to run the same checks locally.

## CI/CD Workflows

- **`test.yml`**: Runs the test suite with `pytest` and static analysis (`mypy`, `ty`, `ruff`).
- **`lint.yml`**: Enforces consistent code style with `ruff`, `flake8`, and `pylint`.
- **`typecheck.yml`**: Validates type hints using `mypy`, `ty`, `pyright`, and `pytype`.
- **`code-quality.yml`**: Scans for security vulnerabilities and complex code
  with `Bandit`, `Safety`, `Radon`, and `Xenon`.
- **`pre-commit.yml`**: Validates the `.pre-commit-config.yaml` file.

## Local Development

### Pre-commit Hooks

Use pre-commit hooks to catch issues early. They run `ruff`, `mypy`, and
security checks automatically on commit.

```bash
pre-commit install
pre-commit run --all-files
```

### Manual Execution

Run checks manually:

```bash
# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/simple_resume/ --strict
uv run ty check src/simple_resume/

# Testing
uv run pytest
```

## Configuration

All workflows use Python 3.10 and `uv`. Security and complexity scan reports are
saved as build artifacts in GitHub Actions.
