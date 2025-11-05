# Getting Started Guide

This guide explains how to create your first resume with Simple-Resume.

## Table of Contents

- [Installation](#installation)
- [Creating Your Resume](#creating-your-resume)
- [Understanding the YAML Structure](#understanding-the-yaml-structure)
- [Customizing Your Resume](#customizing-your-resume)
- [Next Steps](#next-steps)

## Installation

### Prerequisites

1.  **Python 3.9+**: Check with `python --version`.
2.  **uv**: See the [uv installation guide](https://github.com/astral-sh/uv).
3.  **wkhtmltopdf**: Required for PDF generation.
    -   macOS: `brew install wkhtmltopdf`
    -   Ubuntu/Debian: `sudo apt-get install wkhtmltopdf`
    -   Windows: Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/).

### Install Simple-Resume

```bash
# Clone the repository
git clone https://github.com/athola/simple-resume.git
cd simple-resume

# Install dependencies
uv sync
```

## Creating Your Resume

### 1. Start with a Sample

The easiest way to start is to copy one of the sample files:

```bash
cp sample/input/sample_1.yaml my_resume.yaml
```

### 2. Add Your Information

Open `my_resume.yaml` in a text editor and replace the sample content with your own. The YAML structure is straightforward:

```yaml
full_name: "Your Name"
job_title: "Your Job Title"
email: "your.email@example.com"
# ...and so on

body:
  experience:
    - company: "Your Company"
      position: "Your Position"
      # ...
```

For a detailed explanation of all the available fields, see the comments in the sample files.

### 3. Generate Your Resume

You can generate your resume in either HTML or PDF format.

```bash
# Generate an HTML resume and open it in your browser
uv run simple-resume generate --format html --open

# Generate a PDF resume and open it
uv run simple-resume generate --format pdf --open
```

You can also generate multiple resumes at once by placing multiple YAML files in a directory and using the `--data-dir` flag.

## Customizing Your Resume

You can customize the look and feel of your resume through the `config` section of your YAML file.

### Templates

Simple-Resume comes with a few built-in templates:

- `resume_no_bars`: A clean, minimalist design.
- `resume_with_bars`: A design that includes skill level bars.

```yaml
config:
  template: "resume_no_bars"
```

### Color Schemes

You can use one of the built-in color schemes or define your own.

```yaml
# Use a built-in scheme
config:
  color_scheme: "Professional Blue"

# Or define your own colors
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

For more details on theming, see the [Color Schemes guide](wiki/Color-Schemes.md).

## Next Steps

- [Markdown Guide](wiki/Markdown-Guide.md): Learn how to use Markdown to format your resume content.
- [Examples](../sample/): Browse the sample resume files for more ideas.

## Troubleshooting

If you run into trouble, here are a few common solutions:

- **PDF generation fails**: Make sure `wkhtmltopdf` is installed correctly and available in your system's PATH. You can check this by running `wkhtmltopdf --version`.
- **YAML syntax errors**: Use an online YAML validator to check your file for syntax errors. Pay close attention to indentation (we recommend 2 spaces).

If you're still stuck, please open an issue on [GitHub](https://github.com/athola/simple-resume/issues).
