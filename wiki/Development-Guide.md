# Development Guide

This guide covers setting up a local development environment for Simple-Resume.

## Setup

1.  Fork and clone the repository.
2.  Install dependencies:

    ```bash
    uv sync
    ```

## Running Checks

We use a `Makefile` for common development tasks.

### Testing

Run unit and integration tests:

```bash
make test
```

### Code Quality

We use `ruff` for linting and formatting.

Run all checks (linting, formatting, type-checking):

```bash
make check-all
```

Or run individual checks:

```bash
make lint
make format
```

## Contributing

Before contributing, read our [Contributing Guide](Contributing.md) for information on the development process and submitting pull requests.
