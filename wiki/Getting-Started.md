# Getting Started

This guide explains how to create your first resume with Simple-Resume.

## Table of Contents

- [Installation](#installation)
- [Creating Your Resume](#creating-your-resume)
- [Customizing Your Resume](#customizing-your-resume)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.9+
- uv

### Install Simple-Resume

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume
uv sync
```

## Creating Your Resume

1.  **Start with a Sample**: Copy `sample/input/sample_1.yaml` to `my_resume.yaml`.

    ```bash
    cp sample/input/sample_1.yaml my_resume.yaml
    ```

2.  **Add Your Information**: Open `my_resume.yaml` and replace the sample content. The YAML structure is straightforward. Refer to comments in the sample files for field explanations.

    ```yaml
    full_name: "Your Name"
    job_title: "Your Job Title"
    email: "your.email@example.example.com"
    # ...and so on

    body:
      experience:
        - company: "Your Company"
          position: "Your Position"
          # ...
    ```

3.  **Generate Your Resume**: Generate your resume in HTML or PDF format.

    ```bash
    uv run simple-resume generate --format html --open
    uv run simple-resume generate --format pdf --open
    ```

    You can generate multiple resumes by placing several YAML files in a directory and using the `--data-dir` flag.

## Customizing Your Resume

Customize your resume's appearance using the `config` section in your YAML file.

### Templates

Simple-Resume includes these built-in templates:

-   `resume_no_bars`: A minimalist design.
-   `resume_with_bars`: Includes skill level bars.

To use a template:

```yaml
config:
  template: "resume_no_bars"
```

### Color Schemes

Use built-in color schemes or define your own. See the [Color Schemes guide](Color-Schemes.md) for details.

To use a built-in scheme:

```yaml
config:
  color_scheme: "Professional Blue"
```

## Next Steps

-   [Markdown Guide](Markdown-Guide.md): Format your resume content with Markdown.
-   [Examples](../sample/): Explore sample resume files for more ideas.

## Troubleshooting

Common issues and solutions:

-   **PDF generation fails**: Ensure `wkhtmltopdf` is installed and in your system's PATH. Check with `wkhtmltopdf --version`.
-   **YAML syntax errors**: Validate your YAML file with an online validator. Pay attention to 2-space indentation.

If you're still stuck, open an issue on [GitHub](https://github.com/athola/simple-resume/issues).
