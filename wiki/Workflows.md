# GitHub Actions Workflows

This project uses GitHub Actions to automate code quality checks. These checks run on every push and pull request to the `main` branch. This guide overviews each workflow and explains local execution of the same checks.

## CI/CD Workflows

-   **`test.yml`**: Runs `pytest` test suite; performs static analysis with `mypy`, `ty`, `ruff`.
-   **`lint.yml`**: Enforces consistent code style using `ruff`, `flake8`, `pylint`.
-   **`typecheck.yml`**: Validates type hints using `mypy`, `ty`, `pyright`, `pytype`.
-   **`code-quality.yml`**: Scans for security vulnerabilities, code complexity with `Bandit`, `Safety`, `Radon`, `Xenon`.
-   **`pre-commit.yml`**: Validates `.pre-commit-config.yaml` file.

## Local Development

### Pre-commit Hooks

Pre-commit hooks are recommended to identify issues before committing code. Hooks run `ruff`, `mypy`, and several security checks automatically.

```bash
# Install the pre-commit hooks
uv run pre-commit install

# Run the hooks on all files
uv run pre-commit run --all-files
```

### Manual Execution

You can also run the checks manually.

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

All workflows use Python 3.9 and `uv`. Security and complexity scan reports save as build artifacts in GitHub Actions.
