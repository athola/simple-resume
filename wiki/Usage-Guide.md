# Usage Guide

This guide provides instructions for using the command-line interface (CLI) and Python API.

## Command-Line Interface

The `simple-resume` CLI is the primary tool for generating resumes.

### Generating Resumes

The `generate` command creates a resume in the specified format.

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

The `--data-dir` argument processes all YAML files in a directory.

```bash
uv run simple-resume generate --data-dir my_resumes --format html
```

## Python API

The `generate` and `preview` functions can be imported for programmatic use.

### Generating Resumes Programmatically

The `generate` function takes a resume file path and a `GenerationConfig` object.

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

The `preview` function opens a resume in a web browser without saving it to a file.

```python
from simple_resume import preview

preview("resume_private/input/my_resume.yaml", open_after=True)
```

## Customization

### LaTeX Output

To generate a `.tex` file for use with a LaTeX engine, set `output_mode: latex` in the `config` section of your YAML file. This provides full control over typesetting, custom fonts, and mathematical equations, and is ideal for academic and research applications.

```yaml
config:
  output_mode: latex
```

When this setting is enabled, the `generate` command will produce a `.tex` file instead of an HTML or PDF file.

#### LaTeX Requirements

A LaTeX distribution must be installed on your system. The following are recommended:
- **TeX Live** (cross-platform)
- **MiKTeX** (Windows)
- **MacTeX** (macOS)

#### Compilation

Once the `.tex` file has been generated, it can be compiled with a LaTeX engine.

```bash
# 1. Generate the LaTeX source file.
uv run simple-resume generate

# 2. Compile the .tex file with a LaTeX engine.
pdflatex resume_output.tex
```

For better font support, `xelatex` or `lualatex` can be used.

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

For more information, see the [Color Schemes Guide](Color-Schemes.md).

### Layout

The layout of template elements can be adjusted in the `config` section of the YAML file. Values are specified in CSS units (e.g., `mm`).

```yaml
config:
  section_icon_circle_size: "7.8mm"
  section_icon_circle_x_offset: "-0.5mm"
  section_icon_design_size: "4mm"
  section_icon_design_x_offset: "-0.1mm"
  section_icon_design_y_offset: "-0.4mm"
  section_heading_text_margin: "-6mm"
```

## Validation

The tool validates the following fields:

-   `full_name`: Must not be empty.
-   `email`: Must be a valid email address.
-   Date fields: Must be in `YYYY` or `YYYY-MM` format.
