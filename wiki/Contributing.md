# Contributing Guide

This guide explains how to contribute to the `simple-resume` project. We welcome bug reports, feature suggestions, and code improvements.

## Reporting Bugs and Suggesting Features

Bugs and feature suggestions should be reported by opening a GitHub issue.

-   **[Report a bug](https://github.com/athola/simple-resume/issues)**: Provide a detailed description of the bug and steps to reproduce it.
-   **[Suggest a feature](https://github.com/athola/simple-resume/issues/new?template=feature_request.md)**: Describe your idea and explain why it would be a good addition to the project.

## Contributing Code

To contribute code, please follow these steps:

1.  Fork the repository and clone it to your local machine.
2.  Create a new branch for your changes.
3.  Set up your development environment by following the [Development Guide](Development-Guide.md).
4.  Make your changes, and add tests and documentation as needed.
5.  Run all code quality checks to ensure that your changes meet our standards.

    ```bash
    make check-all
    make validate
    ```

6.  Push your changes to your fork and open a pull request against the `main` branch.

## Development Guidelines

-   **Code Style**: This project uses `ruff` for linting and formatting. Run `make format` before committing your changes, and maintain consistency with the existing code style.
-   **Tests**: New features must be accompanied by tests. Bug fixes must include a test that demonstrates the bug and its resolution.
-   **Documentation**: All new or changed features must be documented.
