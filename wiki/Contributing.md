# Contributing Guide

This guide explains how to contribute to the `simple-resume` project. Contributions, including bug reports, feature suggestions, and code improvements, are welcome.

## Reporting Bugs and Suggesting Features

Report bugs or suggest new features by opening a GitHub issue.

-   **[Report a bug](https://github.com/athola/simple-resume/issues)**: Please provide a detailed description of the bug, including steps to reproduce it.
-   **[Suggest a feature](https://github.com/athola/simple-resume/issues/new?template=feature_request.md)**: Describe your idea and why you think it would be a good addition to the project.

## Contributing Code

To contribute code, follow these steps:

1.  Fork the repository and clone it to your local machine.
2.  Create a new branch for your changes.
3.  Set up your development environment by following the [Development Guide](Development-Guide.md).
4.  Make your changes. Be sure to add tests and update the documentation if necessary.
5.  Run all code quality checks to ensure your changes meet our standards.

    ```bash
    make check-all
    make validate
    ```

6.  Push your changes to your fork and open a pull request against the `main` branch.

## Development Guidelines

-   **Code Style**: This project uses `ruff` for linting and formatting. Run `make format` before committing changes. Maintain consistency with the existing codebase style.
-   **Tests**: New features require tests. Bug fixes must include a test demonstrating the bug and its resolution.
-   **Documentation**: Update relevant documentation when adding or changing features.
