# Usage Guide

This guide explains how to use Simple-Resume from the command line to generate professional resumes.

## Generating Resumes

You can generate your resume in either HTML or PDF format.

```bash
# Generate a PDF resume
uv run simple-resume generate --format pdf

# Generate an HTML resume
uv run simple-resume generate --format html
```

> ℹ️ Resumes configured with `config.output_mode: latex` are skipped by the HTML CLI. Use the PDF generator when you want to render those LaTeX templates.

### Key Options

-   `--data-dir PATH`: Specify a custom directory for your input and output files. The default is `resume_private`.
-   `--open`: Automatically open the generated resume in the default viewer.
-   `--browser BROWSER`: Specify a browser to use for opening HTML resumes (e.g., "firefox", "chromium").

## LaTeX Output

To generate a LaTeX version of your resume, set the `output_mode` in your YAML file to `latex`:

```yaml
config:
  output_mode: latex
```

This will create a `.tex` file that you can compile with any LaTeX engine.

## Color Customization

You can customize the colors of your resume in the `config` section of your YAML file.

### Using a Preset Scheme

The easiest way to change the look of your resume is to use one of the built-in color schemes:

```yaml
config:
  color_scheme: "Professional Blue"
```

### Defining Custom Colors

You can also define your own colors:

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

For a full list of available color properties and preset schemes, see the [Color Schemes Guide](Color-Schemes.md).
