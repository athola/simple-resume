# GitHub Actions Workflows

This project uses GitHub Actions to automate code quality checks on every push and pull request to the `main` branch. This guide provides an overview of each workflow and explains how to run the same checks locally.

## CI/CD Workflows

-   **`test.yml`**: Runs the `pytest` test suite and performs static analysis with `mypy`, `ty`, and `ruff`.
-   **`lint.yml`**: Enforces a consistent code style using `ruff`, `flake8`, and `pylint`.
-   **`typecheck.yml`**: Validates type hints using `mypy`, `ty`, `pyright`, and `pytype`.
-   **`code-quality.yml`**: Scans for security vulnerabilities and code complexity with `Bandit`, `Safety`, `Radon`, and `Xenon`.
-   **`pre-commit.yml`**: Validates the `.pre-commit-config.yaml` file.

## Local Development

### Pre-commit Hooks

Pre-commit hooks are recommended for identifying issues before committing code. The hooks run `ruff`, `mypy`, and several security checks automatically.

```bash
# Install the pre-commit hooks
uv run pre-commit install

# Run the hooks on all files
uv run pre-commit run --all-files
```

### Manual Execution

The checks can also be run manually.

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

All workflows use Python 3.9 and `uv`. Security and complexity scan reports are saved as build artifacts in GitHub Actions.
