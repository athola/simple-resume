# Usage Guide

This guide covers the command-line interface (CLI) and Python API.

## Command-Line Interface

The `simple-resume` CLI generates resumes.

### Generating Resumes

The `generate` command creates a resume in a specified format.

```bash
# Generate a PDF file
uv run simple-resume generate --format pdf

# Generate an HTML file
uv run simple-resume generate --format html
```

The `--open` flag opens the generated file automatically.

```bash
uv run simple-resume generate --format pdf --open
```

The `--browser` flag specifies a browser for opening HTML files.

```bash
uv run simple-resume generate --format html --browser firefox
```

### Specifying a Data Directory

The `--data-dir` argument processes all YAML files within a specified directory.

```bash
uv run simple-resume generate --data-dir my_resumes --format html
```

### JSON Resume Import

simple-resume supports importing JSON Resume files (`.json` from jsonresume.org). Drop a JSON Resume file into your input directory and `simple-resume` will automatically convert it at load time.

**Schema reference**: v1.0.x JSON Resume schema is supported.

```bash
# Place your JSON Resume in the input folder
cp my-resume.json resume_private/input/

# Generate - automatic conversion happens at load time
uv run simple-resume generate --format pdf
```

The importer converts:

- Key content (basics, work, education, projects)
- JSON Resume highlights to markdown bullet points
- Required simple-resume structure (template, config)
- JSON Resume fields to simple-resume equivalents

**Field mapping** (partial):

| JSON Resume | simple-resume |
|-------------|---------------|
| `basics.name` | `full_name` |
| `basics.email` | `email` |
| `basics.phone` | `phone` |
| `basics.url` | `web` |
| `work[]` | `body.Experience` |
| `education[]` | `body.Education` |
| `projects[]` | `body.Projects` |
| `skills[]` | `body.Skills` |

The conversion is not 1:1 — some JSON Resume fields may not map directly. Review the converted output and adjust as needed.

### ATS Resume Screening

The `screen` command scores a resume against a job description using multiple NLP algorithms.

```bash
# Basic screening with text output
uv run simple-resume screen my_resume.yaml job_description.txt

# Generate a YAML report
uv run simple-resume screen my_resume.yaml job.txt --format yaml --output report.yaml

# Use specific scorer only
uv run simple-resume screen resume.yaml job.txt --scorers tfidf

# Verbose output with detailed breakdown
uv run simple-resume screen resume.yaml job.txt --verbose
```

**Output formats:**
- `text` (default): Human-readable text report
- `yaml`: Structured YAML report for automation
- `json`: Machine-readable JSON report

**Scorer options:**
- `all` (default): Uses TF-IDF, Jaccard, and Keyword scorers combined
- `tfidf`: Statistical term frequency analysis only
- `jaccard`: N-gram phrase overlap only
- `keyword`: Exact keyword matching only

**Exit codes:**
- `0`: Score >= 50% (passing)
- `1`: Score < 50% or error occurred

## Python API

Import the `generate` and `preview` functions for programmatic use.

### API Stability Guarantees

All symbols exported from `simple_resume` and `simple_resume.api.*` modules are covered by semantic versioning guarantees:

- **Stable**: No breaking changes within a major version
- **Documented**: Public APIs include docstrings
- **Typed**: Full type annotations for IDE support

Internal modules (`simple_resume.core.*`, `simple_resume.shell.*`) are implementation details and may change without notice.

### Generating Resumes Programmatically

The `generate` function accepts a resume file path and a `GenerationConfig` object.

```python
from simple_resume import generate
from simple_resume.core.models import GenerationConfig

# Generate both PDF and HTML formats
results = generate(
    "resume_private/input/my_resume.yaml",
    GenerationConfig(formats=["pdf", "html"])
)
```

### Previewing Resumes

The `preview` function opens a resume in your web browser without saving it to a file.

```python
from simple_resume import preview

preview("resume_private/input/my_resume.yaml", open_after=True)
```

## Customization

### LaTeX Output

Set `output_mode: latex` in the `config` section of your YAML file to generate a `.tex` file. This allows for typesetting, custom fonts, and mathematical equations, often used for academic and research applications.

```yaml
config:
  output_mode: latex
```

When this setting is enabled, the `generate` command will produce a `.tex` file instead of an HTML or PDF file.

#### LaTeX Requirements

Install a LaTeX distribution:
- **TeX Live** (cross-platform)
- **MiKTeX** (Windows)
- **MacTeX** (macOS)

#### Compilation

Compile the generated `.tex` file with a LaTeX engine.

```bash
# 1. Generate the LaTeX source file.
uv run simple-resume generate

# 2. Compile the .tex file with a LaTeX engine.
pdflatex resume_output.tex
```

For better font support, use `xelatex` or `lualatex`.

```bash
xelatex resume_output.tex
lualatex resume_output.tex
```

### Colors

A color scheme can be specified in the YAML file or as a command-line argument.

```yaml
# In the YAML file
config:
  color_scheme: "Professional Blue"
```

```bash
# From the command line
uv run simple-resume generate --palette resume_private/palettes/my-theme.yaml
```

See the [Color Schemes Guide](Color-Schemes.md).

### Layout

The layout of template elements can be adjusted in the `config` section of the YAML file. Icon-related values are specified as numbers (unit: mm).

```yaml
config:
  section_icon_circle_size: 7.8
  section_icon_circle_x_offset: -0.5
  section_icon_design_size: 4
  section_icon_design_x_offset: -0.1
  section_icon_design_y_offset: -0.4
  section_heading_text_margin: -6
```

### Typography

Font sizes can be customized in the `config` section. Values are specified in points (pt).

```yaml
config:
  description_font_size: 8.5   # Body text in experience/education entries
  date_font_size: 9            # Primary date labels
  sidebar_font_size: 8.5       # Sidebar content
  bold_font_weight: 600        # Weight for bold text
```

## Validation

The tool validates the following fields:

-   `full_name`: Must not be empty.
-   `email`: Must be a valid email address.
-   Date fields: Must be in `YYYY` or `YYYY-MM` format.
