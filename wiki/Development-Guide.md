# Development Guide

This guide explains how to set up a local development environment for Simple-Resume.

## Setup

1.  **Fork and clone the repository.**

2.  **Install dependencies:**

    ```bash
    # This will create a virtual environment and install all necessary packages
    uv sync
    ```

## Running Checks

We use a `Makefile` to provide convenient commands for common development tasks.

### Testing

To run our full suite of unit and integration tests:

```bash
make test
```

### Code Quality

We use `ruff` for linting and formatting. To check your code for style issues and format it correctly:

```bash
# Run all checks (linting, formatting, type-checking, etc.)
make check-all

# Or run individual checks
make lint
make format
```

## Contributing

Before you start working on a contribution, please read our [Contributing Guide](Contributing.md) for information on our development process and how to submit a pull request.