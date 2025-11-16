# Development Guide

This guide explains how to set up a local development environment for `simple-resume`.

First, fork and clone the repository. This project uses `uv` for dependency management. To install all development and optional dependencies, run the following command:

```bash
uv sync --dev --extra utils
```

## Running Code Quality Checks

The `Makefile` provides commands for running common development tasks.

### Running Tests

To run the full test suite, including unit and integration tests, use the following command:

```bash
make test
```

### Linting and Formatting

The `ruff` tool is used for linting and code formatting. To run all checks, including linting, formatting, type-checking, and security scans, use the following command:

```bash
make check-all
make validate  # Validates the README preview and release assets.
```

Individual checks can also be run:

```bash
# Run the linter
make lint

# Format the code
make format
```

## Architecture

The project uses a **functional core, imperative shell** pattern to separate pure data transformations from code that produces side effects.

-   **Functional Core (`src/simple_resume/core/`)**: Contains pure functions for data manipulation. These functions are predictable and do not have side effects, which makes them easy to test.
-   **Imperative Shell (`src/simple_resume/shell/`)**: Manages I/O, user interaction, and integrations with external services. Side effects are handled in this layer.
-   **API Surface (`src/simple_resume/`)**: The public API provides an interface for reading and writing resume data (e.g., `read_yaml()`, `to_pdf()`).

### Key Components

-   **`Resume` class**: The main entry point for the public API. It provides methods such as `read_yaml()`, `to_pdf()`, and `to_html()`.
-   **`ResumeSession`**: A class that manages configuration settings for consistency across multiple operations.
-   **Palette System**: A system for color management that supports built-in themes, remote palettes, and generated color schemes.
-   **Template System**: Uses Jinja2 for HTML and LaTeX templating.
-   **Validation**: A validation layer that provides error messages for configuration and data issues.

## Testing

The project maintains over 85% test coverage with unit and integration tests.

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run tests with coverage
make test-coverage
```

## Documentation

The project documentation is organized into the following key areas:

-   **[Architecture Decisions (ADRs)](../architecture/)**: Records the history and reasoning behind significant technical decisions.
-   **[Usage Guide](Usage-Guide.md)**: Explains how to use the library's features with practical examples.
-   **[Migration Guide](Migration-Guide-Generate-Module.md)**: Provides instructions for upgrading between major versions.
-   **[Lazy Loading Guide](Lazy-Loading-Guide.md)**: Describes performance optimization strategies.
-   **[API Reference](../docs/reference.md)**: A reference for the public API.

When contributing to the documentation, please adhere to the following best practices:

-   Use clear and concise language.
-   Include code examples for all major features.
-   Document both lazy and eager loading approaches.
-   Explain performance trade-offs.
-   Provide migration paths for breaking changes.
-   Update ADRs for significant architectural changes.
-   Keep docstrings up to date.

## Contributing

Please read the [Contributing Guide](Contributing.md) for information on the development process, coding standards, and how to submit pull requests.

### Development Workflow

1.  Create a feature branch from `main`.
2.  Make your changes and add tests.
3.  Run `make check-all` and `make validate` to ensure that all automated checks pass.
4.  Submit a pull request with a clear description of your changes.
