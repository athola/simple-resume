# Getting Started

This guide outlines the steps to install the tool, create a resume, and generate output files.

## Installation

Requires Python 3.9+ and `uv` installed.

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

    Copy one of the sample files to use as a starting point.
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

    Run the following command to generate HTML and PDF versions of your resume. The `--open` flag will open the files in your browser and default PDF viewer.

    ```bash
    uv run simple-resume generate --format html --open
    uv run simple-resume generate --format pdf --open
    ```

    To generate multiple resumes at once, you can use the `--data-dir` argument with a path to a directory containing multiple YAML files.

## Customization

### Templates

You can change the resume's layout by specifying a different template in your YAML file.

```yaml
template: resume_no_bars  # A minimalist design
# template: resume_with_bars  # A design that includes skill level bars
```

### Color Schemes

Set a color scheme by adding the `color_scheme` key under `config`.

```yaml
config:
  color_scheme: "Professional Blue"
```

For more details, see the [Color Schemes guide](Color-Schemes.md).

## Next Steps

- [Markdown Guide](Markdown-Guide.md): Learn how to format content with Markdown.
- [Examples](../sample/): Review the sample resume files for more examples.

## Troubleshooting

-   **PDF generation fails**: `simple-resume` uses `wkhtmltopdf` to generate PDFs. Install `wkhtmltopdf` and ensure it's in your system's `PATH`.
-   **YAML syntax errors**: YAML requires correct indentation. Validate your YAML syntax with a tool if errors occur.

For questions, open an issue on [GitHub](https://github.com/athola/simple-resume/issues).
