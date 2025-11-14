# Getting Started

This guide provides a hands-on walkthrough to install `simple-resume`, create your first resume from a YAML file, and generate it as a PDF or HTML document.

## 1. Installation and Setup

First, ensure you have Python 3.9+ and `uv` installed.

Then, clone the repository and install the required dependencies:

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume
uv sync
```

## 2. Create and Generate Your Resume

Now you're ready to create and generate your resume.

### Start with a Sample

Copy a sample file to use as a starting point for your own resume. This is the easiest way to get started.

```bash
cp sample/input/sample_1.yaml resume_private/input/my_resume.yaml
```

### Edit the Content

Open `resume_private/input/my_resume.yaml` in your favorite editor and replace the placeholder content with your own information.

```yaml
full_name: "Your Name"
job_title: "Your Job Title"
email: "your.email@example.com"
# ... and so on
```

### Generate the Output

Run the `generate` command to create your resume. The `--open` flag will automatically open the generated file.

```bash
# Generate an HTML resume
uv run simple-resume generate --format html --open

# Generate a PDF resume
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

## 3. Customize Your Resume

You can easily customize the appearance of your resume.

### Change the Template

Change the resume's layout by specifying a different `template` in your YAML file.

```yaml
template: resume_no_bars  # A minimalist design
# template: resume_with_bars  # A design that includes skill level bars
```

### Apply a Color Scheme

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

## Troubleshooting Common Issues

-   **PDF Generation Fails**: PDF creation relies on WeasyPrint or LaTeX. Ensure their dependencies are installed correctly.
-   **YAML Syntax Errors**: YAML is sensitive to indentation. Use a YAML linter in your editor to catch syntax errors.
-   **Template Not Found**: Double-check that the `template` name in your YAML file matches an available template (e.g., `resume_base`, `resume_no_bars`).

For other issues, please open an issue on [GitHub](https://github.com/athola/simple-resume/issues).
