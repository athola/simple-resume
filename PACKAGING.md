# Packaging for PyPI

This guide outlines the process for preparing, building, and publishing `simple-resume` releases to PyPI.

## Prerequisites

-   Python 3.9+
-   `uv` (installed globally)
-   A PyPI account with access to the project.
-   A clean git working directory.

## Versioning

This project uses [Semantic Versioning](https://semver.org/). Before creating a release, update the version in `pyproject.toml` and `CHANGELOG.md`.

## Release Checklist

1.  **Freeze features**: Merge the release branch into `main`.
2.  **Update artifacts**: Update `CHANGELOG.md`, `README.md`, and `assets/preview.jpg` (if the UI has changed).
3.  **Bump the version**: Manually update the version in `pyproject.toml`.
4.  **Regenerate the lockfile**: If dependencies have changed, run the following command:

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

## Building and Verifying the Package

1.  Build the `sdist` and `wheel`:

    ```bash
    uv build
    ```

2.  Check the built packages for errors:

    ```bash
    uv run twine check dist/*
    ```

3.  Install the wheel in a new virtual environment to test it:

    ```bash
    uv venv --python 3.9 --name packaging-smoke
    uv run --venv packaging-smoke pip install dist/simple-resume-X.Y.Z-py3-none-any.whl
    uv run --venv packaging-smoke simple-resume --help
    ```

## Publishing the Package

### Trusted Publishing (Preferred Method)

The GitHub Actions workflow is configured to automatically build and publish a release to PyPI when a new tag is pushed to the `main` branch.

### Manual Publishing

To publish the package manually, use `uv`.

```bash
# Publish to PyPI
uv publish --repository pypi

# Alternatively, publish to TestPyPI first for verification
uv run twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ simple-resume==X.Y.Z
```

## Post-Release Tasks

-   Create a new release on GitHub for the new tag.
-   Close the current milestone and create a new one for the next release.
-   Verify that the package metadata is correct on PyPI.
