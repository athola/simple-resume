# Development Guide

This guide sets up a local development environment for `simple-resume`.

## Environment Setup

1.  **Fork and clone the repository:**

    Fork the repository on GitHub, then clone it locally.

2.  **Install dependencies:**

    This project uses `uv` for dependency management. Install all development and optional dependencies with:

    ```bash
    uv sync --dev --extra utils
    ```

## Running Code Quality Checks

A `Makefile` simplifies common development tasks.

### Running Tests

Run the full test suite, including unit and integration tests, with:

```bash
make test
```

### Linting and Formatting

`ruff` handles linting and code formatting. Run all checks, including linting, formatting, and type-checking, with:

```bash
make check-all
```

You can also run individual checks:

```bash
# Run the linter
make lint

# Format the code
make format
```

## Contributing

Before starting, read the [Contributing Guide](Contributing.md) for information on the development process, coding standards, and submitting pull requests.
