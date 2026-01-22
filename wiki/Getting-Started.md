# Getting Started

This guide explains how to install `simple-resume`, create a resume from a YAML file, and generate PDF or HTML output.

## 1. Installation and Setup

This guide covers setting up a local development environment. For standard user installation, see the [README.md](../README.md).

First, verify you have Python 3.9+ and `uv` installed. Then, clone the repository and install the required dependencies:

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume
uv sync
```

## 2. Create and Generate Your Resume

### Start with a Sample

Copy one of the sample files to the `resume_private/input` directory.

```bash
cp sample/input/sample_1.yaml resume_private/input/my_resume.yaml
```

### Import from JSON Resume

```bash
# Copy a JSON Resume file (from jsonresume.org)
cp my-resume.json resume_private/input/

# Generate - automatic conversion happens at load time
uv run simple-resume generate --format pdf
```

See [Usage Guide](Usage-Guide.md#json-resume-import) for complete JSON Resume documentation.

### Edit the Content

Open `resume_private/input/my_resume.yaml` in a text editor and replace the placeholder content with your own information.

```yaml
full_name: "Your Name"
job_title: "Your Job Title"
email: "your.email@example.com"
# ... and so on
```

### Generate the Output

Use the `generate` command to create your resume. The `--open` flag will open the generated file in your default browser or PDF viewer.

```bash
# Generate an HTML resume
uv run simple-resume generate --format html --open

# Generate a PDF resume
uv run simple-resume generate --format pdf --open
```

To generate multiple resumes at once, use the `--data-dir` argument to specify a directory containing your YAML files.

## 3. Customize Your Resume

Customize the resume's appearance by editing the YAML file.

### Change the Template

To change the layout of your resume, specify a different `template` in your YAML file.

```yaml
template: resume_no_bars  # A minimalist design
# template: resume_with_bars  # A design with skill level bars
```

### Template Variables

Templates have access to the following variables from your YAML file:

| Variable | Description |
|----------|-------------|
| `name` | Full name |
| `title` | Job title |
| `contact` | Contact information |
| `summary` | Professional summary |
| `experience` | Work experience list |
| `education` | Education list |
| `skills` | Skills list |
| `colors` | Color palette values |

### Apply a Color Scheme

To apply a color scheme, add the `color_scheme` key to the `config` section of your YAML file.

```yaml
config:
  color_scheme: "Professional Blue"
```

See the [Color Schemes guide](Color-Schemes.md).

## Next Steps

- [Markdown Guide](Markdown-Guide.md): Learn how to format content with Markdown.
- [Examples](../sample/): Review the sample resume files for more examples.

## Sample Files

-   **`sample_1.yaml`** and **`sample_2.yaml`**: Basic resume examples.
-   **`sample_multipage_demo.yaml`**: Multi-page resume with pagination.
-   **`sample_palette_demo.yaml`**: Demonstrates various color schemes.
-   **`sample_dark_sidebar.yaml`**: Dark theme with a sidebar layout.
-   **`sample_latex.yaml`**: LaTeX-specific formatting.
-   **`sample_contrast_demo.yaml`**: Color contrast accessibility.

## Troubleshooting

-   **PDF Generation Fails**: PDF generation depends on WeasyPrint or LaTeX. Verify dependencies are installed correctly.
-   **YAML Syntax Errors**: YAML is sensitive to indentation. Use a YAML linter to check for syntax errors.
-   **Template Not Found**: Verify the `template` name in your YAML file matches an available template (e.g., `resume_base`, `resume_no_bars`).

Report other issues on [GitHub](https://github.com/athola/simple-resume/issues).
