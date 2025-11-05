# Packaging Simple-Resume for PyPI

This guide outlines the process for preparing, building, and publishing Simple-Resume releases to PyPI.

## Prerequisites

-   Python 3.12
-   `uv` installed globally
-   A PyPI account with access to the project
-   A clean git status

## Versioning

We use [Semantic Versioning](https://semver.org/). Before a release, update the version in `pyproject.toml` and `CHANGELOG.md`.

## Release Checklist

1.  **Freeze features**: Merge the release branch.
2.  **Update artifacts**:
    -   `CHANGELOG.md`
    -   `README.md`
    -   `assets/preview.jpg` (if the UI has changed)
3.  **Bump the version**:
    ```bash
    # You can do this manually in pyproject.toml
    # or with a script if we add one.
    ```
4.  **Regenerate the lockfile** (if dependencies have changed):
    ```bash
    uv lock --upgrade
    ```
5.  **Run quality checks**:
    ```bash
    make validate
    ```
6.  **Commit and tag**:
    ```bash
    git commit -am "chore: release vX.Y.Z"
    git tag vX.Y.Z
    git push origin main --tags
    ```

## Building and Verifying

Build the sdist and wheel:

```bash
uv build
```

Check the built packages:

```bash
uv run twine check dist/*
```

Install the wheel in a clean virtual environment and test it:

```bash
uv venv --python 3.12 --name packaging-smoke
uv run --venv packaging-smoke pip install dist/simple-resume-X.Y.Z-py3-none-any.whl
uv run --venv packaging-smoke simple-resume --help
```

## Publishing

### Trusted Publishing (Preferred)

Our GitHub Actions workflow will automatically build and publish the release to PyPI when a new tag is pushed.

### Manual Publishing

If you need to publish manually:

```bash
# Publish to PyPI
uv publish --repository pypi

# Or, to TestPyPI first
uv run twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ simple-resume==X.Y.Z
```

## Post-release Tasks

-   Create a GitHub release for the new tag.
-   Close the current milestone and create a new one for the next release.
-   Verify the package metadata on PyPI.

## Automating Future Releases

We plan to automate the release process further by:

-   Creating a `release` GitHub workflow that triggers on new tags.
-   Configuring trusted publishing in PyPI.
-   Using `uv publish` in the CI pipeline.