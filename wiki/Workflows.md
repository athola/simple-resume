# GitHub Actions Workflows

We use GitHub Actions to automatically check our code for errors, style issues, and security vulnerabilities. These checks run on every push and pull request to the `main` branch to help us maintain a healthy codebase. This guide explains what each workflow does and how to run the same checks on your local machine.

## CI/CD Workflows

- **`test.yml`**: Runs our full test suite with `pytest` and does a quick static analysis pass with `mypy`, `ty`, and `ruff`. This is the most important check to ensure everything works as expected.
- **`lint.yml`**: Enforces consistent code style and catches common mistakes using `ruff`, `flake8`, and `pylint`.
- **`typecheck.yml`**: Runs a suite of type checkers (`mypy`, `ty`, `pyright`, and `pytype`) to validate our type hints.
- **`code-quality.yml`**: Scans for potential security vulnerabilities and overly complex code using `Bandit`, `Safety`, `Radon`, and `Xenon`.
- **`pre-commit.yml`**: A simple check to make sure the `.pre-commit-config.yaml` file itself is valid.

## Local Development

### Pre-commit Hooks

The easiest way to catch issues early is to use our pre-commit hooks. They run `ruff`, `mypy`, and security checks automatically every time you make a commit.

```bash
pre-commit install                # Install hooks
pre-commit run --all-files        # Run hooks on all files
```

### Manual Execution

You can also run any of the checks manually.

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

All workflows are configured to use Python 3.10 and `uv`. Reports from the security and complexity scans are saved as build artifacts in GitHub Actions.