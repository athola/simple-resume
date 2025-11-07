# Contributing

This guide outlines how to contribute to the Simple-Resume project.

## Reporting Bugs and Suggesting Features

Open an issue on GitHub to:

- **[Report a bug](https://github.com/athola/simple-resume/issues)**: Provide a detailed report.
- **[Suggest a feature](https://github.com/athola/simple-resume/issues/new?template=feature_request.md)**:
  Describe your idea in detail.

## Contributing Code

To contribute code:

1. Fork and clone the repository.
2. Create a new branch for your changes.
3. Set up your development environment using the [Development Guide](Development-Guide.md).
4. Make your changes, add tests, and update documentation as needed.
5. Run all checks:

    ```bash
    make check-all
    ```

6. Push your changes to your fork and open a pull request to the `main` branch.

## Guidelines

- **Code Style**: Follow existing style. Use `ruff` for linting and formatting (`make lint`, `make format`).
- **Tests**: All new code requires corresponding tests.
- **Documentation**: Update documentation for new or changed features.
