# GitHub Actions Workflows

This project uses GitHub Actions to automate code quality checks on every push and pull request to the `main` branch. This guide provides an overview of each workflow and explains how to run the same checks locally.

## CI/CD Workflows

-   **`test.yml`**: Runs the `pytest` test suite and performs static analysis with `mypy`, `ty`, and `ruff`.
-   **`lint.yml`**: Enforces consistent code style using `ruff`, `flake8`, and `pylint`.
-   **`typecheck.yml`**: Validates type hints with `mypy`, `ty`, `pyright`, and `pytype`.
-   **`code-quality.yml`**: Scans for security vulnerabilities and code complexity with `Bandit`, `Safety`, `Radon`, and `Xenon`.
-   **`pre-commit.yml`**: Validates the `.pre-commit-config.yaml` file.
-   **`publish-packages.yml`**: Publishes the package to PyPI when version changes are detected on the `main` branch.
-   **`release.yml`**: Creates GitHub releases automatically when version tags are pushed.

## Local Development

### Pre-commit Hooks

Pre-commit hooks identify issues before committing code. They automatically run `ruff`, `mypy`, and several security checks.

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

## Release Workflow

The `release.yml` workflow automates GitHub release creation when tags are pushed.

### Creating a Release

```bash
# Tag the version (must start with 'v')
git tag v0.1.2
git push origin v0.1.2
```

The workflow performs the following actions:

1. Builds the package using `uv build`
2. Extracts version information from the tag
3. Generates a changelog from commits since the previous tag
4. Creates a GitHub release with:
   - Generated changelog
   - Installation instructions
   - Built distribution artifacts (`.tar.gz` and `.whl` files)
   - Prerelease flag for tags containing `alpha`, `beta`, or `rc`

### Package Publishing

The `publish-packages.yml` workflow monitors the `main` branch for version changes in `pyproject.toml`. When a version change is detected:

1. Builds and verifies the package distributions
2. Publishes to PyPI (requires `PYPI_API_TOKEN` secret)

## Configuration

All workflows use Python 3.9 and `uv`. Security and complexity scan reports become build artifacts in GitHub Actions.
