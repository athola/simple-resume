# Usage Guide

This guide explains how to use Simple-Resume from the command line to generate resumes.

## Generating Resumes

You can generate your resume in HTML or PDF format:

```bash
# Generate a PDF resume
uv run simple-resume generate --format pdf

# Generate an HTML resume
uv run simple-resume generate --format html
```

> ℹ️ Resumes with `config.output_mode: latex` are skipped by the HTML CLI. Use the PDF generator to render LaTeX templates.

### Key Options

- `--data-dir PATH`: Specify a custom directory for input and output files (default: `resume_private`).
- `--open`: Automatically open the generated resume.
- `--browser BROWSER`: Specify a browser for opening HTML resumes (e.g., "firefox", "chromium").

## Python API

You can also generate resumes from Python:

```python
from simple_resume import generate, preview

# Render PDF and HTML
results = generate("resume_private/input/my_resume.yaml", formats=("pdf", "html"))

# Launch an HTML preview in your browser
preview("resume_private/input/my_resume.yaml", open_after=True)
```

These helpers use the same configuration overrides as the CLI.

## LaTeX Output

To generate a LaTeX version of your resume, set the `output_mode` in your YAML file to `latex`:

```yaml
config:
  output_mode: latex
```

This creates a `.tex` file that you can compile with a LaTeX engine.

## Color Customization

You can customize the colors of your resume using preset schemes, custom colors, or standalone palette files. For detailed instructions and examples, see the [Color Schemes Guide](Color-Schemes.md).

To use a preset color scheme:

```yaml
config:
  color_scheme: "Professional Blue"
```

To use a standalone palette file:

```bash
uv run simple-resume generate --palette palettes/my-theme.yaml
```

## Validation

Simple-Resume requires the following fields in your resume YAML:

- `full_name`: Must not be empty.
- `email`: Must be a valid email address.
- Date fields (e.g., `start_date`, `end_date`) must be in `YYYY` or `YYYY-MM` format.

If validation fails, you will get an error message that points to the incorrect field.
