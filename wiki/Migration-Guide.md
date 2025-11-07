# Migration Guide

This guide explains how to migrate to the latest version of Simple-Resume. The new architecture features a more robust design, improved error handling, and a powerful programmatic API, with the CLI consolidated under the `simple-resume` command.

## Table of Contents

- [Who Should Read This](#who-should-read-this)
- [Breaking Changes Summary](#breaking-changes-summary)
- [Quick Migration Example](#quick-migration-example)
- [Detailed Migration Steps](#detailed-migration-steps)
- [New Features](#new-features)
- [Migration Checklist](#migration-checklist)
- [Getting Help](#getting-help)

## Who Should Read This

-   **CLI Users** (Low Impact): If you only use the command-line tools, switch to the consolidated command (`uv run simple-resume generate …`). You'll primarily need to update your YAML files.
-   **Programmatic Users** (High Impact): If you import Simple-Resume functions in Python code, update imports and API calls to use the new `simple_resume.generation` module.
-   **Custom Template Authors** (Medium Impact): If you maintain custom Jinja2 templates, you may need minor syntax updates for dictionary access.

## Breaking Changes Summary

| Component | Previous Behavior | New Requirement | Action Required |
|-----------|-------------------|-----------------|-----------------|
| **YAML Structure** | `template` inside `config` block | `template` at root level | Move `template` key out of `config` |
| **Programmatic API** | Import from `generate_pdf`/`generate_html` | Import from `simple_resume.generation` | Update import statements and function calls |
| **Jinja2 Templates** | Dot notation for dict access | Bracket notation for dict access | Update custom templates: `group["items"]` |
| **Error Handling** | Generic exceptions | Specific exception hierarchy | Update exception catches (optional) |
| **CLI Entry Points** | Direct Python file execution | Unified `simple-resume` command | Use `uv run simple-resume generate --format pdf` instead of Python file execution |

## Quick Migration Example

### For CLI Users

#### YAML File Changes

The `template` property moved from the `config` section to the root of the YAML file.

**Before (v0.0.x):**

```yaml
config:
  template: resume_with_bars
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

**After (v0.2.0+):**

```yaml
template: resume_with_bars
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

#### Command Line Changes

Commands now use proper entry points.

**Before (v0.0.x):**

```bash
# Old direct Python file execution
uv run python src/simple_resume/generate_pdf.py --data-dir resume_private
uv run python src/simple_resume/generate_html.py --open
```

**After (v0.2.0+):**

```bash
# Unified CLI command
uv run simple-resume generate --format pdf --data-dir resume_private
uv run simple-resume generate --format html --open
```

### For Programmatic Users

#### Python API Changes

The API has been restructured with a new functional interface.

**Before (v0.0.x):**

```python
from simple_resume.generation import generate_pdf as generate_pdf_cli

# Old approach: Call CLI function directly
generate_pdf_cli()  # programmatic entry point now exposed via generation module
```

**After (v0.2.0+):**

```python
from simple_resume.generation import generate_pdf

# New approach: Use functional API with result objects
result = generate_pdf(name="my_resume", data_dir="resume_private")

if result.is_success():
    print(f"Generated: {result.output_path}")
else:
    print(f"Error: {result.error}")
```

#### Batch Processing Example

```python
from simple_resume.session import ResumeSession
from simple_resume.generation import generate_pdf

with ResumeSession(data_dir="resumes/") as session:
    for resume_name in ["resume_1", "resume_2", "resume_3"]:
        result = session.generate_pdf(resume_name)
        print(f"{resume_name}: {result.status}")
```

## Detailed Migration Steps

### Step 1: Update YAML Files

**Action**: Move the `template` property from `config` to the root level.

**Reason**: This separates structural choices (template) from styling choices (colors).

**Migration Script** (optional):

```bash
# Find all YAML files that need updating
find . -name "*.yaml" -exec grep -l "config:" {} \;

# Manual update recommended:
# 1. Open each YAML file
# 2. Cut the "template: xyz" line from config section
# 3. Paste it at the root level
```

**Validation**:

```bash
# Test your updated YAML files
uv run simple-resume generate --format pdf --data-dir your_dir
```

### Step 2: Update Custom Templates

**Action**: Replace dot notation with bracket notation for dictionary access.

**Applies to**: Custom Jinja2 templates only.

**Before (v0.0.x):**

```jinja2
{% for item in group.items %}
  <li>{{ item.title }}: {{ item.description }}</li>
{% endfor %}
```

**After (v0.2.0+):**

```jinja2
{% for item in group["items"] %}
  <li>{{ item["title"] }}: {{ item["description"] }}</li>
{% endfor %}
```

**Reason**: The new data model requires bracket notation for consistency.

### Step 3: Update Programmatic Code

**Action**: Migrate from CLI imports to the new generation API.

**Applies to**: Python scripts that use `import simple_resume`.

**Before (v0.0.x):**

```python
# Old CLI-style import
from simple_resume.generation import generate_pdf as generate_resume_pdf
from simple_resume.utilities import load_yaml_data

data = load_yaml_data("resume.yaml")
pdf_path = generate_resume_pdf(data, "output.pdf")
```

**After (v0.2.0+):**

```python
# New functional API
from simple_resume.generation import generate_pdf
from simple_resume.core.resume import Resume

# Option 1: Generate from name (recommended)
result = generate_pdf(name="resume", data_dir=".")
if result.is_success():
    print(f"PDF saved to: {result.output_path}")

# Option 2: Generate from Resume object (advanced)
resume = Resume.from_yaml("resume.yaml")
resume.hydrate()  # Process markdown, apply theme
result = resume.to_pdf("output.pdf")
```

### Step 4: Update Error Handling

**Action**: Catch specific exceptions instead of generic ones.

**Applies to**: Programmatic users who handle errors.

**Before (v0.0.x):**

```python
try:
    generate_pdf_cli()  # programmatic entry point now exposed via generation module
except Exception as e:
    print(f"Error: {e}")
```

**After (v0.2.0+):**

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

The v0.2.0+ release introduces these new features:

### Fluent API

Chain operations on `Resume` objects for more readable code:

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

Process multiple resumes efficiently with shared configuration:

```python
from simple_resume.session import ResumeSession

with ResumeSession(data_dir="resumes/") as session:
    for name in ["resume_tech", "resume_academic"]:
        result = session.generate_pdf(name)
```

**Benefit**: Session management reuses template compilation and reduces I/O overhead by ~40% for batch operations.

### Rich Result Objects

Get detailed feedback from generation operations:

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

Programmatically generate color palettes:

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

See the [Color Schemes Guide](Color-Schemes.md) for details.

### LaTeX Rendering Support

Generate LaTeX documents alongside HTML/PDF:

```yaml
config:
  output_mode: latex
```

```bash
uv run simple-resume generate --format pdf --data-dir resumes
```

## Migration Checklist

Use this checklist to track your migration progress:

### CLI Users

- [ ] Update all YAML files: move `template` to root level
- [ ] Test generation with `uv run simple-resume generate --format pdf --data-dir your_dir`
- [ ] Update documentation/scripts that reference old command syntax
- [ ] If using custom templates, update dictionary access to bracket notation
- [ ] Verify output matches expectations

### Programmatic Users

- [ ] Update imports from `generate_pdf`/`generate_html` to `simple_resume.generation`
- [ ] Replace CLI function calls with new API functions
- [ ] Update error handling to use specific exception classes
- [ ] Consider adopting session management for batch operations
- [ ] Review and update any custom template code
- [ ] Update tests to verify new API behavior
- [ ] Update documentation/comments referencing old API

### Template Authors

- [ ] Update custom templates: replace dot notation with bracket notation
- [ ] Test templates with new data model
- [ ] Verify all template variables are accessible
- [ ] Update template documentation

## Deprecation Timeline

| Version | Status | Notes |
|---------|--------|-------|
| **v0.0.x** | Deprecated | Old CLI scripts and imports still work but emit warnings |
| **v0.1.x** | Current | New API recommended; old API deprecated |
| **v0.2.x** | Planned | Old API removed; migration required |

**Recommendation**: Migrate to the new API now to avoid breaking changes in v0.2.0.

## Getting Help

If you encounter issues during migration:

1.  Review the [Usage Guide](Usage-Guide.md) and [Development Guide](Development-Guide.md).
2.  Search for similar problems in [GitHub Issues](https://github.com/athola/simple-resume/issues).
3.  Open a new issue or start a [Discussion](https://github.com/athola/simple-resume/discussions).
4.  If reporting a bug, include:
    -   Your Simple-Resume version
    -   Sample YAML file (sanitized)
    -   Error message or unexpected behavior
    -   Steps to reproduce
