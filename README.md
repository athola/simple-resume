<p align="center">
  <a href="https://github.com/athola/simple-resume">
    <img src="assets/preview.png" alt="Simple-Resume - Professional Resume Generator" width="600">
  </a>
</p>

<p align="center">
  <i>A lightweight, CLI-based tool for creating professional, print-ready resumes from structured YAML data.</i>
</p>

<p align="center">
  <a href="https://github.com/athola/simple-resume/actions/workflows/CI.yml">
    <img src="https://github.com/athola/simple-resume/workflows/CI/badge.svg" alt="CI Status">
  </a>
  <a href="https://codecov.io/gh/athola/simple-resume">
    <img src="https://codecov.io/gh/athola/simple-resume/branch/main/graph/badge.svg" alt="Code Coverage">
  </a>
  <a href="https://github.com/athola/simple-resume/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  </a>
  <a href="https://pypi.org/project/simple-resume/">
    <img src="https://img.shields.io/pypi/v/simple-resume.svg" alt="PyPI Version">
  </a>
</p>

# Simple-Resume

Simple-Resume is a Python package for generating print-ready resumes from simple YAML files. Instead of fighting with word processors, you can define your resume's content in a structured way and let this tool handle the formatting.

## Features

- **YAML-based**: Define your resume content in a simple, human-readable format.
- **CLI-driven**: Automate resume generation from the command line.
- **HTML & PDF Output**: Generate both a web-friendly HTML page and a print-ready PDF.
- **Custom Themes**: Customize your resume's appearance with different color palettes.
- **LaTeX Support**: Render your resume with the power and quality of LaTeX.
- **Markdown Formatting**: Use Markdown to format text in your resume sections.

## Getting Started

To get started, check out the **[Getting Started Guide](wiki/Getting-Started.md)** in our project wiki. It will walk you through setting up your environment and creating your first resume.

## Usage

Simple-Resume is run from the command line:

```bash
# Generate PDF resumes
uv run simple-resume generate --format pdf [--data-dir PATH] [--open]

# Generate HTML resumes
uv run simple-resume generate --format html [--data-dir PATH] [--open] [--browser BROWSER]
```

> ℹ️ The HTML CLI skips resumes configured for LaTeX output (`config.output_mode: latex`). Use the PDF CLI when you want to render LaTeX templates.

For more details on advanced features like color customization and LaTeX output, see the **[Usage Guide](wiki/Usage-Guide.md)**.

## Documentation

All our documentation is in the [project wiki](https://github.com/athola/simple-resume/wiki). Here are some key pages:

- **[Markdown Guide](wiki/Markdown-Guide.md)**: Learn how to format your resume content.
- **[Color Schemes](wiki/Color-Schemes.md)**: Customize the look of your resume.
- **[Development Guide](wiki/Development-Guide.md)**: Set up a development environment and run tests.
- **[Contributing Guide](wiki/Contributing.md)**: Learn how to contribute to the project.

## Contributing

We welcome contributions! If you'd like to help improve Simple-Resume, please see our **[Contributing Guide](wiki/Contributing.md)** for detailed instructions.

### Quick Start

1.  **Fork the repository.**
2.  **Create a feature branch**: `git checkout -b feature/your-amazing-feature`
3.  **Set up your environment** by following the [Development Guide](wiki/Development-Guide.md).
4.  **Make your changes** and add tests for any new functionality.
5.  **Run all checks**: `make check-all`
6.  **Submit a pull request.**

All contributions should pass our quality checks, maintain test coverage, and follow the existing code style.

## Community

- **[GitHub Issues](https://github.com/athola/simple-resume/issues)**: Report bugs or request features.
- **[GitHub Discussions](https://github.com/athola/simple-resume/discussions)**: Ask questions and share ideas.

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
