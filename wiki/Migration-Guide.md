# Migration Guide

This guide explains migrating to the latest `simple-resume` version. The new version features improved error handling, a new programmatic API, and a consolidated CLI under the `simple-resume` command.

## Who Should Read This

-   **CLI Users** (Low Impact): If you only use command-line tools, switch to the new `simple-resume generate` command and update YAML files.
-   **Programmatic Users** (High Impact): If you import `simple-resume` functions in Python code, update imports and API calls to use the new `simple_resume.generation` module.
-   **Custom Template Authors** (Medium Impact): If you maintain custom Jinja2 templates, minor syntax updates for dictionary access may be required.

## Breaking Changes Summary

| Component | Previous Behavior | New Requirement | Action Required |
|-----------|-------------------|-----------------|-----------------|
| **YAML Structure** | `template` key was inside `config` block. | `template` key is now at root level. | Move `template` key out of `config` block. |
| **Programmatic API** | Functions imported from `generate_pdf`, `generate_html`. | Functions now imported from `simple_resume.generation`. | Update import statements, function calls. |
| **Jinja2 Templates** | Dictionary access used dot notation. | Dictionary access now uses bracket notation. | Update custom templates to use bracket notation (e.g., `group["items"]`). |
| **Error Handling** | Library raised generic exceptions. | Library now has specific exception hierarchy. | Update `try...except` blocks for specific exceptions (optional). |
| **CLI Entry Points** | CLI invoked by directly executing Python files. | CLI now invoked through unified `simple-resume` command. | Use `uv run simple-resume generate --format pdf` instead of direct Python file execution. |

## Quick Migration Example

### For CLI Users

#### YAML File Changes

The `template` property moved from the `config` section to the YAML file's root.

**Before (v0.0.x):**

```yaml
config:
  template: resume_with_bars
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

**After (v0.1.0+):**

```yaml
template: resume_with_bars
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

#### Command-Line Changes

The commands now use a single entry point.

**Before (v0.0.x):**

```bash
# Old direct Python file execution
uv run python src/simple_resume/generate_pdf.py --data-dir resume_private
uv run python src/simple_resume/generate_html.py --open
```

**After (v0.1.0+):**

```bash
# Unified CLI command
uv run simple-resume generate --format pdf --data-dir resume_private
uv run simple-resume generate --format html --open
```

### For Programmatic Users

#### Python API Changes

The API restructured for greater functionality.

**Before (v0.0.x):**

```python
from simple_resume.generation import generate_pdf as generate_pdf_cli

# Old approach: Call CLI function directly
generate_pdf_cli()
```

**After (v0.1.0+):**

```python
from simple_resume.generation import generate_pdf

# New approach: Use the functional API with result objects
result = generate_pdf(name="my_resume", data_dir="resume_private")

if result.is_success():
    print(f"Generated: {result.output_path}")
else:
    print(f"Error: {result.error}")
```

#### Batch Processing Example

```python
from simple_resume.session import ResumeSession

with ResumeSession(data_dir="resumes/") as session:
    for resume_name in ["resume_1", "resume_2", "resume_3"]:
        result = session.generate_pdf(resume_name)
        print(f"{resume_name}: {result.status}")
```

## Detailed Migration Steps

### Step 1: Update YAML Files

**Action**: Move the `template` property from the `config` block to the root level of YAML files.

**Reason**: This change separates structural (template) from styling (colors) configuration.

**Validation**:

```bash
# Test your updated YAML files
uv run simple-resume generate --format pdf --data-dir your_dir
```

### Step 2: Update Custom Templates

**Action**: In custom Jinja2 templates, replace dot notation with bracket notation for dictionary access.

**Reason**: New data model requires bracket notation for consistency.

### Step 3: Update Programmatic Usage

**Action**: If using `simple-resume` as a library, migrate code from old CLI-style imports to the new generation API.

**Before (v0.0.x):**

```python
from simple_resume.generation import generate_pdf as generate_resume_pdf
from simple_resume.utilities import load_yaml_data

data = load_yaml_data("resume.yaml")
pdf_path = generate_resume_pdf(data, "output.pdf")
```

**After (v0.1.0+):**

```python
from simple_resume.generation import generate_pdf
from simple_resume.core.resume import Resume

# Option 1: Generate from a file name (recommended)
result = generate_pdf(name="resume", data_dir=".")
if result.is_success():
    print(f"PDF saved to: {result.output_path}")

# Option 2: Generate from a Resume object (advanced)
resume = Resume.from_yaml("resume.yaml")
resume.hydrate()  # Process Markdown and apply the theme
result = resume.to_pdf("output.pdf")
```

### Step 4: Update Error Handling

**Action**: If catching exceptions from `simple-resume`, update code to catch new, more specific exceptions.

**Before (v0.0.x):**

```python
try:
    generate_pdf_cli()
except Exception as e:
    print(f"Error: {e}")
```

**After (v0.1.0+):**

```python
from simple_resume.exceptions import (
    ResumeValidationError,
    TemplateRenderError,
    FileOperationError,
)

try:
    result = generate_pdf(name="resume")
    if not result.is_success():
        print(f"Generation failed: {result.error}")
except ResumeValidationError as e:
    print(f"Invalid YAML data: {e}")
except TemplateRenderError as e:
    print(f"Template error: {e}")
except FileOperationError as e:
    print(f"File I/O error: {e}")
```

**Exception Hierarchy**:

```text
Simple-ResumeError (base)
├── ResumeValidationError    # Invalid YAML structure
├── TemplateRenderError      # Jinja2 rendering issues
├── FileOperationError       # File not found, permission denied
└── PaletteError             # Color scheme issues
```

## New Features

The v0.1.0 release includes these new features:

### Fluent API

Chain operations on `Resume` objects for more readable code.

```python
from simple_resume.core.resume import Resume

resume = (
    Resume.from_yaml("input.yaml")
    .hydrate()
    .apply_palette("Professional Blue")
    .to_pdf("output.pdf")
)
```

### Session Management

The new session management system processes multiple resumes more efficiently with shared configuration, reducing I/O overhead by up to 40% for batch operations.

```python
from simple_resume.session import ResumeSession

with ResumeSession(data_dir="resumes/") as session:
    for name in ["resume_tech", "resume_academic"]:
        result = session.generate_pdf(name)
```

### Rich Result Objects

The generation functions now return detailed result objects.

```python
result = generate_pdf(name="resume")

if result.is_success():
    print(f"Generated: {result.output_path}")
    print(f"  Size: {result.file_size} bytes")
    print(f"  Duration: {result.duration}ms")
else:
    print(f"Failed: {result.error}")
    print(f"  Stage: {result.failed_at}")
```

### Enhanced Color Palette System

Programmatically generate color palettes.

```yaml
# In your YAML file
config:
  palette:
    source: generator
    type: hcl
    size: 6
    seed: 42
    hue_range: [210, 260]
    luminance_range: [0.35, 0.85]
    chroma: 0.12
```

See the [Color Schemes Guide](Color-Schemes.md) for more details.

### LaTeX Rendering Support

Generate LaTeX documents in addition to HTML and PDF.

```yaml
config:
  output_mode: latex
```

```bash
uv run simple-resume generate --format pdf --data-dir resumes
```

## Migration Checklist

Use this checklist to track migration progress.

### CLI Users

- [ ] Update all YAML files: move `template` key to root level.
- [ ] Test generation with new `uv run simple-resume generate` command.
- [ ] Update documentation or scripts referencing old command syntax.
- [ ] If using custom templates, update dictionary access to bracket notation.
- [ ] Verify output matches expectations.

### Programmatic Users

- [ ] Update import statements to use new `simple_resume.generation` module.
- [ ] Replace old CLI function calls with new API functions.
- [ ] Update error handling to use new specific exception classes.
- [ ] Consider using new session management feature for batch operations.
- [ ] Review and update custom template code.
- [ ] Update tests to verify new API behavior.
- [ ] Update documentation or comments referencing old API.

### Template Authors

- [ ] Update your custom templates to use bracket notation instead of dot notation for dictionary access.
-   [ ] Test templates with new data model.
-   [ ] Verify all template variables are accessible.
-   [ ] Update template documentation.

## Deprecation Timeline

| Version | Status | Notes |
|---------|--------|-------|
| **v0.0.x** | Deprecated | Old CLI scripts and imports continue to work but emit warnings. |
| **v0.1.x** | Current | New API recommended. Old API deprecated. |
| **v0.2.x** | Planned | The old API will be removed. |

**Recommendation**: Migrate to the new API soon to avoid breaking changes in future releases.

## Getting Help

If issues arise during migration, follow these steps:

1.  Review the [Usage Guide](Usage-Guide.md) and [Development Guide](Development-Guide.md).
2.  Search for similar issues on [GitHub](https://github.com/athola/simple-resume/issues).
3.  If no solution found, open a new issue or start a [discussion](https://github.com/athola/simple-resume/discussions).
4.  When reporting a bug, include the following information:
    -   The version of `simple-resume` you are using.
    -   A sanitized sample of your YAML file.
    -   The error message or a description of the unexpected behavior.
    -   The steps to reproduce the issue.
