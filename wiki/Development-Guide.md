# Development Guide

To set up a local development environment for `simple-resume`, first fork and clone the repository.

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

`ruff` handles linting and code formatting. Run all checks, including linting, formatting, type-checking, and security scans, with:

```bash
make check-all
make validate  # validates README preview + release assets
```

You can also run individual checks:

```bash
# Run the linter
make lint

# Format the code
make format
```

## Architecture

The project is built on a **functional core, imperative shell** pattern, which separates pure data transformations from code that produces side effects.

-   **Functional Core (`src/simple_resume/core/`)**: Contains pure functions for data manipulation. These functions are predictable and have no side effects, which makes them easy to test.
-   **Imperative Shell (`src/simple_resume/shell/`)**: Manages I/O, user interaction, and integrations with external services. This is where side effects are handled.
-   **API Surface (`src/simple_resume/`)**: The public API provides a clear and consistent interface for reading and writing resume data, inspired by the symmetric I/O patterns found in libraries like pandas (e.g., `read_yaml()`, `to_pdf()`).

### Key Components

-   **`Resume` class**: The main entrypoint for the public API. It provides methods like `read_yaml()`, `to_pdf()`, and `to_html()`.
-   **`ResumeSession`**: A class that manages configuration settings to ensure they are applied consistently across multiple operations.
-   **Palette System**: A flexible system for color management that supports built-in themes, remote palettes from APIs, and procedurally generated color schemes.
-   **Template System**: Uses Jinja2 for HTML and LaTeX templating.
-   **Validation**: A validation layer that provides detailed error messages for configuration and data issues.

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

## Documentation

Project documentation is organized into several key areas:

### Documentation Structure

- **[Architecture Decisions (ADRs)](../architecture/)**: Records the history and reasoning behind significant technical decisions.
- **[Usage Guide](Usage-Guide.md)**: Explains how to use the library's features with practical examples.
- **[Migration Guide](Migration-Guide-Generate-Module.md)**: Provides instructions for upgrading between major versions.
- **[Lazy Loading Guide](Lazy-Loading-Guide.md)**: Describes performance optimization strategies available in the library.
- **[API Reference](../docs/reference.md)**: A comprehensive reference for the public API.

### Key Architecture Decisions

Recent important ADRs to understand:

- **[ADR 008: Constants Consolidation](../architecture/ADR008-constants-consolidation.md)** - Why constants were reorganized
- **[ADR 002: Functional Core, Imperative Shell](../architecture/ADR002-functional-core-imperative-shell.md)** - Core architecture pattern
- **[ADR 007: Color Palette System](../architecture/ADR007-color-palette-system.md)** - Color management strategy

### Documentation Best Practices

When contributing:

1. **Update ADRs for significant changes** - Document architectural decisions
2. **Add examples to Usage Guide** - Show practical usage patterns
3. **Create migration guides** - Help users upgrade between versions
4. **Document performance implications** - Include lazy loading considerations
5. **Maintain docstrings** - Keep module and function documentation current

### Writing Documentation

- Use clear, concise language
- Include code examples for all major features
- Document both lazy and eager loading approaches
- Explain performance trade-offs
- Provide migration paths for breaking changes

## Contributing

Before starting, read the [Contributing Guide](Contributing.md) for information on the development process, coding standards, and submitting pull requests.

### Development Workflow

1. Create a feature branch from main
2. Make your changes with comprehensive tests
3. Run `make check-all` and `make validate` to ensure all automated checks pass
4. Submit a pull request with clear description of changes
