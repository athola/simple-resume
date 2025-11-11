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

## Architecture

This project follows a **functional core, imperative shell** architecture pattern:

- **Core**: Pure functions in `src/simple_resume/core/` that handle data transformations without side effects
- **Shell**: Imperative code in `src/simple_resume/shell/` that handles I/O, user interaction, and external dependencies
- **API Surface**: Public API in `src/simple_resume/` provides a pandas-like interface with symmetric I/O patterns

### Key Components

-   **`Resume` class**: Main API with pandas-like methods (`read_yaml()`, `to_pdf()`, `to_html()`)
-   **`ResumeSession`**: Manages consistent configuration across multiple operations
-   **Palette system**: Supports built-in, remote, and procedurally generated color schemes
-   **Template system**: Jinja2-based templates with LaTeX support
-   **Validation**: Comprehensive validation with detailed error reporting

## Testing

The project maintains >85% test coverage with comprehensive unit and integration tests:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run tests with coverage
make test-coverage
```

## Contributing

Before starting, read the [Contributing Guide](Contributing.md) for information on the development process, coding standards, and submitting pull requests.

### Development Workflow

1. Create a feature branch from main
2. Make your changes with comprehensive tests
3. Run `make check-all` to ensure all checks pass
4. Submit a pull request with clear description of changes
