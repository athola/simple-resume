# Contributing to Simple-Resume

This guide outlines how to contribute to the Simple-Resume project.

## Reporting Bugs and Suggesting Features

To report a bug or suggest a feature, please open an issue on GitHub:

-   **[Report a bug](https://github.com/athola/simple-resume/issues)**: If you find a bug, please provide a detailed report so we can fix it.
-   **[Suggest a feature](https://github.com/athola/simple-resume/issues/new?template=feature_request.md)**: If you have an idea for a new feature, please describe it in detail.

## Contributing Code

If you'd like to contribute code, here's how to get started:

1.  **Fork the repository** and clone it to your local machine.
2.  **Create a new branch** for your changes.
3.  **Set up your development environment** by following the [Development Guide](Development-Guide.md).
4.  **Make your changes.** Be sure to add tests for any new code and update the documentation if necessary.
5.  **Run all checks** to make sure your code is ready for review:
    ```bash
    make check-all
    ```
6.  **Push your changes** to your fork and **open a pull request** to the `main` branch of the Simple-Resume repository.

## Guidelines

-   **Follow the existing code style.** We use `ruff` for linting and formatting, which you can run with `make lint` and `make format`.
-   **Write tests.** All new code should have corresponding tests.
-   **Update the documentation.** If you add a new feature or change an existing one, please update the documentation.