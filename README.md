![Simple-Resume preview screenshot](assets/preview.png)

_A CLI tool for generating resumes from YAML files._

[![Code Quality](https://github.com/athola/simple-resume/workflows/Code%20Quality/badge.svg)](
  https://github.com/athola/simple-resume/actions/workflows/code-quality.yml
)
[![Linting](https://github.com/athola/simple-resume/workflows/Linting/badge.svg)](
  https://github.com/athola/simple-resume/actions/workflows/lint.yml
)
[![Test Suite](https://github.com/athola/simple-resume/workflows/Test%20Suite/badge.svg)](
  https://github.com/athola/simple-resume/actions/workflows/test.yml
)
[![Code Coverage](https://codecov.io/gh/athola/simple-resume/branch/main/graph/badge.svg)](
  https://codecov.io/gh/athola/simple-resume
)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](
  https://github.com/athola/simple-resume/blob/main/LICENSE
)
[![PyPI Version](https://img.shields.io/pypi/v/simple-resume.svg)](
  https://pypi.org/project/simple-resume/
)
[![Open Bugs](https://img.shields.io/github/issues/athola/simple-resume/bug.svg)](
  https://github.com/athola/simple-resume/issues?q=is%3Aopen+is%3Aissue+label%3Abug
)
[![Open Pull Requests](https://img.shields.io/github/issues-pr/athola/simple-resume.svg)](
  https://github.com/athola/simple-resume/pulls
)

# simple-resume

`simple-resume` is a command-line tool and Python library for generating PDF, HTML, and LaTeX resumes from a YAML source file. It is designed to help you maintain a version-controlled resume and easily switch between different templates and color schemes.

## Getting Started

### Installation

To install the latest stable version, run one of the following commands:

```bash
# Install with uv (recommended)
uv add simple-resume

# Install with pip
pip install simple-resume
```

### Development Setup

To set up a development environment, clone the repository and install the project in editable mode with development dependencies.

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume

# Install for development with uv
uv sync --dev --extra utils

# Install for development with pip
pip install -e .[dev,utils]
```

## Quick Start

First, create a YAML file to store your resume content. The `template` field specifies which base template to use.

```yaml
# resume_private/input/my_resume.yaml

# The base template to use for the resume.
template: resume_base

# Your personal information.
full_name: Jane Doe
job_title: Software Engineer
address:
  - 123 Tech Street
  - San Francisco, CA
phone: "(555) 123-4567"
email: jane.doe@example.com
web: https://jandoe.dev
linkedin: in/janedoe
github: janedoe

# A short description of your professional background.
description: |
  Software engineer with 5+ years of experience building scalable
  web applications and leading cross-functional teams.

# The main body of your resume.
body:
  experience:
    - title: Senior Software Engineer
      company: TechCorp
      start: 2022
      end: Present
      description: |
        * Led development of microservices architecture serving 1M+ users
        * Mentored junior developers and conducted code reviews
        * Improved system performance by 40% through optimization

  skills:
    - Python
    - JavaScript
    - React
    - Node.js
    - PostgreSQL
    - Docker
    - AWS
```

### Generate from the Command Line

Use the `simple-resume generate` command to create your resume in PDF or HTML format.

```bash
# Generate a PDF version of your resume.
uv run simple-resume generate --format pdf

# Generate an HTML version and open it in your browser.
uv run simple-resume generate --format html --open
```

### Use the Python API

The library provides a clean Python API for programmatic resume generation.

```python
from simple_resume import generate, preview

# Quick generation - just pass a YAML file path
result = generate("my_resume.yaml")
print(f"Generated: {result['pdf'].output_path}")

# Preview in browser
preview("my_resume.yaml")  # Opens HTML in default browser

# Generate multiple formats
from simple_resume.shell.generate import GenerateOptions

options = GenerateOptions(
    formats=["pdf", "html"],
    template="resume_with_bars",
    open_after=True,
)
results = generate("my_resume.yaml", options)
```

#### Session-based API

For more control or batch operations, use a session:

```python
from simple_resume import Resume
from simple_resume.shell.session import ResumeSession

# Direct, single-file conversion
resume = Resume.read_yaml("resume_private/input/my_resume.yaml")
result = resume.to_pdf(open_after=True)

# Session for consistent settings across multiple resumes
with ResumeSession(data_dir="resume_private") as session:
    resume = session.resume("my_resume")

    # Method chaining for configuration
    styled = resume.with_palette("Professional Blue").with_template("resume_base")
    result = styled.to_pdf(open_after=True)

    # Batch generation
    batch_results = session.generate_all(format="pdf", open_after=False)
```

### Customize Styling

Apply a built-in color palette or provide a path to your own.

```bash
# Use a built-in palette
uv run simple-resume generate --palette "Professional Blue"

# Use a custom palette file
uv run simple-resume generate --palette resume_private/palettes/my-theme.yaml
```

### Generate LaTeX for Advanced Typesetting

For full control over typesetting, generate a `.tex` file by setting `output_mode: latex` in your YAML's `config` section. This requires a local LaTeX installation (e.g., TeX Live, MiKTeX).

```bash
# 1. Generate LaTeX source (configured via YAML)
uv run simple-resume generate

# 2. Compile with pdflatex
pdflatex resume_output.tex
```

For detailed LaTeX configuration and examples, see the [LaTeX Output section in the Usage Guide](wiki/Usage-Guide.md#latex-output).

### Use Color Utilities

The core library includes utilities for tasks like calculating accessible text colors.

```python
from simple_resume.core import colors

accent = colors.get_contrasting_text_color("#F6F6F6")
assert accent == "#000000"
```

## Documentation

- **[Getting Started](wiki/Getting-Started.md)**: A detailed guide to installation and basic setup.
- **[Usage Guide](wiki/Usage-Guide.md)**: A comprehensive guide to all features, including templates, palettes, and LaTeX output.
- **[Development Guide](wiki/Development-Guide.md)**: Instructions for setting up a development environment and contributing to the project.
- **[Migration Guide](wiki/Migration-Guide.md)**: Instructions for upgrading from previous versions.
- **[Color Schemes](wiki/Color-Schemes.md)**: A guide to creating and using custom color palettes.
- **[Workflows](wiki/Workflows.md)**: Examples of common use cases and patterns.
- **[API Reference](docs/api/index.md)**: Full reference for the Python API (auto-generated from docstrings).

## Getting Help

For bugs and feature requests, open a GitHub issue. For questions, use GitHub Discussions.

- **[GitHub Issues](https://github.com/athola/simple-resume/issues)**
- **[GitHub Discussions](https://github.com/athola/simple-resume/discussions)**

See `sample/` for more example resume files.

## Contributing

1. Fork repository and create feature branch.
2. Set up environment by following the [Development Guide](wiki/Development-Guide.md).
3. Make changes and add tests.
4. Run `make check-all validate` to run all checks.
5. Submit a pull request.

## License

This project is licensed under the MIT License.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=athola/simple-resume&type=date&legend=top-left)](https://www.star-history.com/#athola/simple-resume&type=date&legend=top-left)
