![Simple-Resume preview screenshot](assets/preview.png)

_A lightweight, CLI-based tool for creating professional, print-ready resumes from
structured YAML data._

[![CI Status](https://github.com/athola/simple-resume/workflows/CI/badge.svg)](
  https://github.com/athola/simple-resume/actions/workflows/CI.yml
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

# Simple-Resume

**Simple-Resume** is a Python package for generating print-ready resumes from YAML files. It separates content from presentation, so you can focus on your resume's substance while the tool handles the formatting. This is useful for developers, people who need multiple resume versions, and anyone who prefers to manage their resume in version control.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Getting Help](#getting-help)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multiple Output Formats**: Generate your resume as a high-quality PDF, a web-friendly HTML file, or a LaTeX file for academic and technical submissions.
- **YAML and Markdown Content**: Define your resume content in YAML for structure and use Markdown for rich text formatting within sections. This makes it easy to manage your resume in version control.
- **Templates and Styling**: Choose from several built-in templates and customize them with color palettes, custom fonts, and adjustable page layouts. You can also create your own reusable color schemes in separate files.
- **Developer-Focused Tools**: Use the CLI for automation and CI/CD integration. The Python API is also available for more complex workflows. The tool is cross-platform and provides clear error messages.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) or pip

### Installation

You can install the package using `uv` or `pip`:

```bash
# Using uv (recommended)
pip install uv
uv add simple-resume

# Using pip
pip install simple-resume
```

To work on the project locally, clone the repository and install it in development mode:

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume

# Install in development mode with uv
uv sync --dev

# Or with pip
pip install -e .
```

## Quick Start

### 1. Create Your Resume Data

Create a YAML file for your resume (e.g., `resume_private/input/my_resume.yaml`):

```yaml
template: resume_base

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

description: |
  Passionate software engineer with 5+ years of experience building scalable
  web applications and leading cross-functional teams.

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

### 2. Generate Your Resume

```bash
# Generate PDF (most common)
uv run simple-resume generate --format pdf

# Generate HTML
uv run simple-resume generate --format html

# Auto-open the generated file
uv run simple-resume generate --format pdf --open
```

### 3. Try the Python Helpers

```python
from simple_resume import generate, preview

# Render multiple formats at once (name inferred from YAML path)
results = generate("resume_private/input/my_resume.yaml", formats=("pdf", "html"))

# Launch an HTML preview in your browser
preview("resume_private/input/my_resume.yaml", open_after=True)
```

### 3. Use Custom Styling

```bash
# Use a built-in color scheme
uv run simple-resume generate --palette "Professional Blue"

# Use a standalone palette file
uv run simple-resume generate --palette sample/palettes/ocean-blue.yaml

# Combine options
uv run simple-resume generate --palette sample/palettes/sunset-warm.yaml --format pdf --open
```

## Usage Examples

### Basic Usage

Generate a PDF or HTML resume:

```bash
uv run simple-resume generate --format pdf
uv run simple-resume generate --format html --open
```

### Advanced Styling

Use a built-in color palette or a custom one:

```bash
uv run simple-resume generate --palette "Professional Blue"
uv run simple-resume generate --palette palettes/my-theme.yaml
```

Customize the page dimensions:

```bash
uv run simple-resume generate --page-width 220 --page-height 310
```

### Batch Processing

Generate multiple resumes with different color schemes:

```bash
for palette in sample/palettes/*.yaml; do
  palette_name=$(basename "$palette" .yaml)
  uv run simple-resume generate --palette "$palette" --output "resume_${palette_name}.pdf"
done
```

## Documentation

The full documentation is in the [project wiki](https://github.com/athola/simple-resume/wiki). The [API Reference](docs/reference.md) documents the public Python API.

Key documents:

- **[Getting Started](wiki/Getting-Started.md)**
- **[Usage Guide](wiki/Usage-Guide.md)**
- **[Development Guide](wiki/Development-Guide.md)**
- **[Contributing Guide](wiki/Contributing.md)**

## Getting Help

- **[GitHub Issues](https://github.com/athola/simple-resume/issues)**: Report bugs and request features.
- **[GitHub Discussions](https://github.com/athola/simple-resume/discussions)**: Ask questions and share ideas.

The `sample/` directory also contains example resume files and configurations.

## Contributing

Contributions are welcome. To get started:

1.  Fork the repository and create a feature branch.
2.  Set up your environment by following the [Development Guide](wiki/Development-Guide.md).
3.  Make your changes and add tests.
4.  Run `make check-all` to run all checks.
5.  Submit a pull request.

For more details, see the [Contributing Guide](wiki/Contributing.md).

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).

---
[Back to top](#simple-resume)
