# Getting Started

This guide covers installing the tool, creating a resume from a YAML file, and generating PDF or HTML output.

## Installation

Prerequisites: Python 3.9+ and `uv` installed.

1.  Clone the repository:

    ```bash
    git clone https://github.com/athola/simple-resume.git
    cd simple-resume
    ```

2.  Install dependencies:

    ```bash
    uv sync
    ```

## Creating Your Resume

1.  **Start with a sample:**

    Copy a sample file to use as a starting point.

    ```bash
    cp sample/input/sample_1.yaml resume_private/input/my_resume.yaml
    ```

2.  **Edit the YAML file:**

    Open `resume_private/input/my_resume.yaml` and replace the placeholder content with your own information.

    ```yaml
    full_name: "Your Name"
    job_title: "Your Job Title"
    email: "your.email@example.com"

    body:
      experience:
        - company: "Your Company"
          position: "Your Position"
    ```

3.  **Generate the resume:**

    Run the following command to generate your resume. The `--open` flag opens the output file in your default application (e.g., browser for HTML, PDF viewer for PDF).

    ```bash
    uv run simple-resume generate --format html --open
    uv run simple-resume generate --format pdf --open
    ```

    To generate multiple resumes at once, point the `--data-dir` argument to a directory containing your YAML files.

### Using the Python API

The tool can also be used as a Python library for programmatic use:

```python
from simple_resume import Resume
from simple_resume.session import ResumeSession

# Load and generate a resume
resume = Resume.read_yaml("resume_private/input/my_resume.yaml")
result = resume.to_pdf(open_after=True)

# Use a session for consistent settings (e.g., data directory)
with ResumeSession(data_dir="resume_private") as session:
    resume = session.resume("my_resume")
    # Apply different styles
    styled_resume = resume.with_palette("Professional Blue").with_template("resume_base")
    result = styled_resume.to_pdf()
```

## Customization

### Templates

You can change the resume's layout by specifying a different template in your YAML file.

```yaml
template: resume_no_bars  # A minimalist design
# template: resume_with_bars  # A design that includes skill level bars
```

### Color Schemes

Apply a color scheme by adding the `color_scheme` key under a `config` section in your YAML.

```yaml
config:
  color_scheme: "Professional Blue"
```

For more details, see the [Color Schemes guide](Color-Schemes.md).

## Next Steps

- [Markdown Guide](Markdown-Guide.md): Learn how to format content with Markdown.
- [Examples](../sample/): Review the sample resume files for more examples.

## Sample Files

The `sample/` directory contains examples demonstrating different features:

-   **`sample_1.yaml`**, **`sample_2.yaml`** - Basic resume examples
-   **`sample_multipage_demo.yaml`** - Multi-page resume with proper pagination
-   **`sample_palette_demo.yaml`** - Demonstrates various color schemes
-   **`sample_dark_sidebar.yaml`** - Dark theme with sidebar layout
-   **`sample_latex.yaml`** - LaTeX-specific formatting examples
-   **`sample_contrast_demo.yaml`** - Color contrast accessibility examples

## Troubleshooting

-   **PDF generation fails**: This tool supports WeasyPrint and LaTeX for PDF creation. Ensure their dependencies are installed.
-   **YAML syntax errors**: YAML is sensitive to indentation. Use a linter or validator to check your syntax.
-   **Template not found**: Check the template name in your YAML file. Available templates include `resume_base`, `resume_no_bars`, and `resume_with_bars`.

For other issues, please open an issue on [GitHub](https://github.com/athola/simple-resume/issues).
