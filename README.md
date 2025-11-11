![Simple-Resume preview screenshot](assets/preview.png)

_A CLI tool for generating resumes from YAML files._

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

This tool generates PDF, HTML, and LaTeX resumes from a single YAML source file. This lets you version-control your resume content and apply different templates or color schemes. Use it as a command-line utility or Python library.

## Getting Started

### Installation

```bash
# Install with uv (recommended)
uv add simple-resume

# Install with pip
pip install simple-resume
```

### Development Setup

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume

# Development install with uv
uv sync --dev --extra utils

# Development install with pip
pip install -e .
```

## Quick Start

### 1. Create Your Resume

Create a YAML file with your resume content. The `template` field specifies which base template to use.

```yaml
# resume_private/input/my_resume.yaml
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
  Software engineer with 5+ years of experience building scalable
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

### 2. Generate Resume

Use `simple-resume generate` to create your resume in PDF or HTML format.

```bash
# Generate a PDF
uv run simple-resume generate --format pdf

# Generate an HTML file
uv run simple-resume generate --format html

# Generate a PDF and open it
uv run simple-resume generate --format pdf --open
```

### 3. Use the Python API

The tool can also be used as a library, providing a chained API for configuration.

```python
from simple_resume import Resume
from simple_resume.session import ResumeSession

# Method 1: Direct, single-file conversion
resume = Resume.read_yaml("resume_private/input/my_resume.yaml")
result = resume.to_pdf(open_after=True)
html_result = resume.to_html()

# Method 2: Use a session for consistent settings across multiple resumes
with ResumeSession(data_dir="resume_private") as session:
    resume = session.resume("my_resume")
    # Apply different styles with method chaining
    dark_resume = resume.with_palette("Professional Blue").with_template("resume_base")
    result = dark_resume.to_pdf(open_after=True)

    # Generate all resumes in batch
    batch_results = session.generate_all(format="pdf", open_after=False)
```

### 4. Custom Styling

Apply a color palette by name or custom palette file path.

```bash
# Use a built-in palette
uv run simple-resume generate --palette "Professional Blue"

# Use a custom palette file
uv run simple-resume generate --palette resume_private/palettes/my-theme.yaml
```

#### LaTeX Support

Generate LaTeX source files for advanced typesetting capabilities. This requires a LaTeX distribution (like TeX Live, MiKTeX, or MacTeX) to be installed on your system.

```yaml
# In your YAML file
config:
  output_mode: latex
```

When `output_mode: latex` is set, the generate command produces a `.tex` file instead of PDF or HTML. This gives you full control over typesetting, custom fonts, mathematical equations, and academic formatting.

```bash
# Generate LaTeX source (configured via YAML)
uv run simple-resume generate

# Compile with pdflatex (requires LaTeX installation)
pdflatex resume_output.tex
```

For detailed LaTeX configuration and examples, see the [LaTeX Output section in the Usage Guide](wiki/Usage-Guide.md#latex-output).

### 5. API Utilities

The API includes color utilities, for example, to calculate an accessible text color for a given background.

```python
from simple_resume.api import colors

accent = colors.calculate_text_color("#F6F6F6")
assert accent == "#000000"
```

## Documentation

- **[Getting Started](wiki/Getting-Started.md)**
- **[Usage Guide](wiki/Usage-Guide.md)**
- **[Development Guide](wiki/Development-Guide.md)**
- **[Migration Guide](wiki/Migration-Guide.md)** - For upgrading from earlier versions
- **[Color Schemes](wiki/Color-Schemes.md)** - For creating and using custom palettes
- **[Workflows](wiki/Workflows.md)** - Common patterns and examples
- **[API Reference](docs/reference.md)**

## Getting Help

For bugs and feature requests, open a GitHub issue. For questions, use GitHub Discussions.

- **[GitHub Issues](https://github.com/athola/simple-resume/issues)**
- **[GitHub Discussions](https://github.com/athola/simple-resume/discussions)**

See `sample/` for more example resume files.

## Contributing

1. Fork repository and create feature branch.
2. Set up environment by following the [Development Guide](wiki/Development-Guide.md).
3. Make changes and add tests.
4. Run `make check-all` to run all checks.
5. Submit a pull request.

## License

This project is licensed under the MIT License.
