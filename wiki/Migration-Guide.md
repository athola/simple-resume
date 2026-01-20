# Migration Guide

This guide covers migrating between `simple-resume` versions.

## Version Navigation

- [v0.0.x → v0.1.0](#v00x--v010-major-api-restructure): Major API restructure
- [v0.1.0 → v0.1.1](#v010--v011-generate-module-reorganization): Generate module reorganization

---

## v0.0.x → v0.1.0: Major API Restructure

This release introduces improved error handling, a new programmatic API, and a consolidated CLI under the `simple-resume` command.

### Who Should Read This

-   **CLI Users** (Low Impact): Switch to the new `simple-resume generate` command and update YAML files.
-   **Programmatic Users** (High Impact): Update imports and API calls to use the new `simple_resume` module.
-   **Custom Template Authors** (Medium Impact): Minor syntax updates for dictionary access may be required.

### Breaking Changes Summary

| Component | Previous Behavior | New Requirement | Action Required |
|-----------|-------------------|-----------------|-----------------|
| **YAML Structure** | `template` key was inside `config` block. | `template` key is now at root level. | Move `template` key out of `config` block. |
| **Programmatic API** | Functions imported from `generate_pdf`, `generate_html`. | Functions now imported from `simple_resume`. | Update import statements, function calls. |
| **Jinja2 Templates** | Dictionary access used dot notation. | Dictionary access now uses bracket notation. | Update custom templates to use bracket notation (e.g., `group["items"]`). |
| **Error Handling** | Library raised generic exceptions. | Library now has specific exception hierarchy. | Update `try...except` blocks for specific exceptions (optional). |
| **CLI Entry Points** | CLI invoked by directly executing Python files. | CLI now invoked through unified `simple-resume` command. | Use `uv run simple-resume generate --format pdf` instead of direct Python file execution. |

### Quick Migration Example

#### For CLI Users

**YAML File Changes** - The `template` property moved from the `config` section to the YAML file's root.

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

**Command-Line Changes:**

```bash
# Before (v0.0.x)
uv run python src/simple_resume/generate_pdf.py --data-dir resume_private

# After (v0.1.0+)
uv run simple-resume generate --format pdf --data-dir resume_private
```

#### For Programmatic Users

**Before (v0.0.x):**

```python
from simple_resume import generate_pdf as generate_pdf_cli
generate_pdf_cli()
```

**After (v0.1.0+):**

```python
from simple_resume import generate_pdf

result = generate_pdf(name="my_resume", data_dir="resume_private")
if result.is_success():
    print(f"Generated: {result.output_path}")
else:
    print(f"Error: {result.error}")
```

### Detailed Migration Steps

#### Step 1: Update YAML Files

Move the `template` property from the `config` block to the root level of YAML files. This separates structural (template) from styling (colors) configuration.

```bash
# Validate your updated YAML files
uv run simple-resume generate --format pdf --data-dir your_dir
```

#### Step 2: Update Custom Templates

In custom Jinja2 templates, replace dot notation with bracket notation for dictionary access.

#### Step 3: Update Programmatic Usage

**Before (v0.0.x):**

```python
from simple_resume import generate_pdf as generate_resume_pdf
from simple_resume.shell.runtime.content import get_content

data = get_content("resume.yaml")
pdf_path = generate_resume_pdf(data, "output.pdf")
```

**After (v0.1.0+):**

```python
from simple_resume import generate_pdf
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

#### Step 4: Update Error Handling

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

**Exception Hierarchy:**

```text
Simple-ResumeError (base)
├── ResumeValidationError    # Invalid YAML structure
├── TemplateRenderError      # Jinja2 rendering issues
├── FileOperationError       # File not found, permission denied
└── PaletteError             # Color scheme issues
```

### New Features in v0.1.0

#### Fluent API

```python
from simple_resume.core.resume import Resume

resume = (
    Resume.from_yaml("input.yaml")
    .hydrate()
    .apply_palette("Professional Blue")
    .to_pdf("output.pdf")
)
```

#### Session Management

```python
from simple_resume.shell.session import ResumeSession

with ResumeSession(data_dir="resumes/") as session:
    for name in ["resume_tech", "resume_academic"]:
        result = session.generate_pdf(name)
```

#### Rich Result Objects

```python
result = generate_pdf(name="resume")

if result.is_success():
    print(f"Generated: {result.output_path}")
    print(f"  Size: {result.file_size} bytes")
    print(f"  Duration: {result.duration}ms")
```

---

## v0.1.0 → v0.1.1: Generate Module Reorganization

This release reorganizes the generate module for improved performance with lazy loading.

### Import Path Changes

**Before:**
```python
from simple_resume.generation import generate_pdf, generate_html, generate_all
from simple_resume.generation import GenerationConfig
```

**After:**
```python
# Recommended: Main API (lazy loaded by default)
from simple_resume import generate_pdf, generate_html, generate_all

# Or direct module access
from simple_resume.shell.generate import generate_pdf, generate_html, generate_all

# GenerationConfig moved to core.models
from simple_resume.core.models import GenerationConfig
```

### Module Structure Changes

The `simple_resume.generation` module has been reorganized into:

```
simple_resume/generate/
├── __init__.py    # Main API exports (lazy loading)
├── core.py        # Eager loading, full functionality
└── lazy.py        # Lazy loading wrappers
```

### Compatibility Matrix

| Previous Import | New Import | Notes |
|----------------|------------|-------|
| `simple_resume.generation` | `simple_resume` | Drop-in replacement |
| `simple_resume.generation.GenerationConfig` | `simple_resume.core.models.GenerationConfig` | Path changed |
| `simple_resume.generation.*functions` | `simple_resume.shell.generate.*functions` | Path changed |

### Lazy vs Eager Loading

#### Lazy Loading (Default)
- **Best for**: CLI tools, scripts, applications where generation is optional
- **Benefits**: Faster startup, lower memory footprint

```python
from simple_resume import generate_pdf  # Lazy loaded
```

#### Eager Loading
- **Best for**: Web applications, services where generation is always used
- **Benefits**: Predictable performance when generation is called

```python
from simple_resume.shell.generate.core import generate_pdf  # Eager loaded
```

### Troubleshooting

**Error**: `ModuleNotFoundError: No module named 'simple_resume.generation'`

```python
# Replace
from simple_resume.generation import generate_pdf

# With
from simple_resume import generate_pdf
```

**Error**: `ImportError: cannot import name 'GenerationConfig'`

```python
# Replace
from simple_resume.generation import GenerationConfig

# With
from simple_resume.core.models import GenerationConfig
```

---

## Migration Checklist

### CLI Users

- [ ] Update YAML files: move `template` key to root level
- [ ] Test with `uv run simple-resume generate` command
- [ ] Update any scripts referencing old command syntax
- [ ] Update bracket notation in custom templates

### Programmatic Users

- [ ] Update import statements to use new `simple_resume` module
- [ ] Replace CLI function calls with new API functions
- [ ] Update error handling for specific exception classes
- [ ] Consider session management for batch operations
- [ ] Update tests to verify new API behavior

### Template Authors

- [ ] Use bracket notation for dictionary access
- [ ] Test templates with new data model
- [ ] Verify all template variables are accessible

---

## API Timeline

| Version | Status | Notes |
|---------|--------|-------|
| **v0.0.x** | Legacy | Previous version with basic functionality |
| **v0.1.x** | Current | Stable API with modern architecture |
| **v0.2.x** | Future | Planned enhancements |

---

## Getting Help

1. Review the [Usage Guide](Usage-Guide.md) and [Development Guide](Development-Guide.md)
2. Search [GitHub Issues](https://github.com/athola/simple-resume/issues)
3. Open a new issue or start a [discussion](https://github.com/athola/simple-resume/discussions)

When reporting issues, include:
- Version of `simple-resume`
- Sanitized sample of your YAML file
- Error message or unexpected behavior
- Steps to reproduce
