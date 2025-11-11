# Usage Guide

This guide provides detailed instructions for using the command-line interface (CLI), Python API, and other features.

## Command-Line Interface

The `simple-resume` CLI is the primary tool for resume generation.

### Generating Resumes

Use the `generate` command to create a resume in the desired format.

```bash
# Generate a PDF file
uv run simple-resume generate --format pdf

# Generate an HTML file
uv run simple-resume generate --format html
```

Automatically open the generated file using the `--open` flag.

```bash
uv run simple-resume generate --format pdf --open
```

Specify a different browser for HTML files using the `--browser` flag.

```bash
uv run simple-resume generate --format html --browser firefox
```

### Specifying a Data Directory

To process multiple YAML files from a single directory, use the `--data-dir` argument.

```bash
uv run simple-resume generate --data-dir my_resumes --format html
```

## Python API

For programmatic use, you can import functions like `generate` and `preview`.

### Generating Resumes Programmatically

The `generate` function accepts a resume file path and a `GenerateOptions` object.

```python
from simple_resume import generate
from simple_resume.generation import GenerateOptions

# Generate both PDF and HTML formats
results = generate(
    "resume_private/input/my_resume.yaml",
    GenerateOptions(formats=("pdf", "html"))
)
```

### Previewing Resumes

The `preview` function opens a resume in your web browser without saving it.

```python
from simple_resume import preview

preview("resume_private/input/my_resume.yaml", open_after=True)
```

## Customization

### LaTeX Output

To generate a `.tex` file for a LaTeX engine, set `output_mode: latex` in your YAML file. This requires a LaTeX distribution to be installed.

With this setting, the `generate` command produces a `.tex` file instead of HTML or PDF.

### Colors

Specify a color scheme in the YAML file or via a command-line argument.

```yaml
# In your YAML file
config:
  color_scheme: "Professional Blue"
```

```bash
# Via the command line
uv run simple-resume generate --palette resume_private/palettes/my-theme.yaml
```

For more information, see the [Color Schemes Guide](Color-Schemes.md).

### Layout

The layout of template elements, like section heading icons, can be adjusted in the `config` section of your YAML. Values are specified in CSS units (e.g., `mm`). Negative values shift elements left/up, while positive values shift them right/down.

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

## Test Framework Helper

The project includes a helper for Behavior-Driven Development (BDD) style tests, intended for internal project development.

The `tests/bdd.py` module provides a `scenario` object for structuring tests.

```python
from tests.bdd import scenario

def test_palette_cli_lists_available_palettes() -> None:
    story = scenario("Palette CLI list command")
    story.given("a registry with sample palettes")
    story.when("the list command runs")

    result = run_cli(["palette", "list"])

    story.then("palette names are printed")
    story.expect("Spectrum Labs" in result, "CLI output should contain palette name")
```

Available methods:

-   `given(step)`, `when(step)`, `then(step)`: Describe the steps of the scenario.
-   `background(**context)`: Add metadata for debugging.
-   `note(message)`: Add optional commentary.
-   `expect(condition, message)`: Perform an assertion.
-   `summary()`: Render the full scenario story.

For more examples, see `tests/unit/test_bdd_helper.py`.
