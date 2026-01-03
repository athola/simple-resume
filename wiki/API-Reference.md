# API Reference

**Version:** 0.1.7
**Last Updated:** 2025-01-03
**Stability:** Public API exports follow semantic versioning guarantees

---

## Table of Contents

- [Stability Contract](#stability-contract)
- [Core Models](#core-models)
- [Exceptions](#exceptions)
- [Generation Functions](#generation-functions)
- [Session Management](#session-management)
- [Result Types](#result-types)
- [Shell I/O Functions](#shell-io-functions)

---

## Stability Contract

The symbols listed in `simple_resume.__all__` are covered by the stability contract:

- ✅ **Stable**: Safe for production use, follows semantic versioning
- ⚠️ **Internal**: Modules under `simple_resume.core.*` and `simple_resume.shell.*` may change without notice
- 🔄 **Lazy-loaded**: Some imports are lazy-loaded for performance; they are still part of the stable API

**Import Guidance:**
```python
# ✅ Correct: Import from public API
from simple_resume import Resume, generate_pdf, ResumeSession

# ⚠️ Not recommended: Internal modules (may break)
from simple_resume.core.resume import Resume  # Works but not guaranteed
from simple_resume.shell.generate import generate_pdf  # May change
```

---

## Core Models

### `Resume`

Domain model representing resume data with pure functional operations.

```python
from simple_resume import Resume

# Load from YAML
resume = Resume.read_yaml("resume.yaml")

# Method chaining
resume = (
    Resume.read_yaml("resume.yaml")
    .with_template("resume_no_bars")
    .with_palette("Professional Blue")
)

# Validate
validation = resume.validate_or_raise()
```

**Methods:**
- `read_yaml(name: str, paths: Paths | None = None) -> Resume` - Factory method
- `with_template(template: str) -> Resume` - Return new Resume with template
- `with_palette(palette: str) -> Resume` - Return new Resume with palette
- `validate_or_raise() -> ValidationResult` - Validate and raise if invalid

### `ResumeConfig`

Normalized resume configuration with validated fields.

```python
from simple_resume import ResumeConfig

config = ResumeConfig(
    template="resume_no_bars",
    theme_color="#0395DE",
    page_width=210,
    page_height=297
)
```

### `RenderPlan`

Pure data structure describing how to render a resume.

```python
from simple_resume import RenderPlan, ResumeConfig

plan = RenderPlan(
    name="my_resume",
    mode="markdown",
    config=ResumeConfig(),
    template_name="resume_no_bars",
    context={...}
)
```

### `ValidationResult`

Result of validating resume data.

```python
from simple_resume import ValidationResult

result = ValidationResult(
    is_valid=True,
    errors=[],
    warnings=["Optional warning"],
    normalized_config=config,
    palette_metadata={...
}
)
```

---

## Exceptions

All exceptions inherit from `SimpleResumeError`.

```python
from simple_resume import (
    SimpleResumeError,
    ValidationError,
    ConfigurationError,
    TemplateError,
    GenerationError,
    PaletteError,
    FileSystemError,
    SessionError,
)
```

| Exception | Usage |
|-----------|-------|
| `SimpleResumeError` | Base exception for all errors |
| `ValidationError` | Invalid resume data or configuration |
| `ConfigurationError` | Missing or invalid configuration |
| `TemplateError` | Template rendering failures |
| `GenerationError` | PDF/HTML generation failures |
| `PaletteError` | Color palette loading failures |
| `FileSystemError` | File I/O errors |
| `SessionError` | Session management errors |

---

## Generation Functions

### `generate_pdf`

Generate PDF resumes using a configuration object.

```python
from simple_resume import generate_pdf, GenerationConfig

config = GenerationConfig(
    name="resume",
    data_dir="resume_private",
    format="pdf"
)

result = generate_pdf(config)
print(f"Generated {result.successful} PDFs")
```

**Returns:** `BatchGenerationResult`

### `generate_html`

Generate HTML resumes using a configuration object.

```python
from simple_resume import generate_html, GenerationConfig

config = GenerationConfig(
    name="resume",
    data_dir="resume_private",
    format="html"
)

result = generate_html(config)
print(f"Generated {result.successful} HTML files")
```

**Returns:** `BatchGenerationResult`

### `generate_all`

Generate resumes in all specified formats.

```python
from simple_resume import generate_all, GenerationConfig

config = GenerationConfig(
    name="resume",
    data_dir="resume_private",
    formats=["pdf", "html"]
)

result = generate_all(config)
# result is a dict: {"pdf": ..., "html": ...}
```

**Returns:** `BatchGenerationResult`

### `generate_resume`

Generate a single resume in a specific format.

```python
from simple_resume import generate_resume, GenerationConfig

config = GenerationConfig(
    name="my_resume",
    format="pdf"
)

result = generate_resume(config)
print(f"Output: {result.output_path}")
```

**Returns:** `GenerationResult`

### `generate`

Render one or more formats for the same source.

```python
from simple_resume import generate

result = generate(
    "resume_private/input/my_resume.yaml",
    formats=["pdf", "html"]
)

for fmt, r in result.items():
    print(f"Generated {fmt}: {r.output_path}")
```

**Returns:** `dict[str, GenerationResult | BatchGenerationResult]`

### `preview`

Render a single resume to HTML and open in browser.

```python
from simple_resume import preview

# Opens in browser automatically
result = preview("resume_private/input/my_resume.yaml")

# Generate only, don't open
result = preview("resume.yaml", open_after=False)
```

**Returns:** `GenerationResult`

---

## Session Management

### `ResumeSession`

Context manager for batch operations with shared configuration.

```python
from simple_resume import ResumeSession, SessionConfig

config = SessionConfig(
    default_template="resume_no_bars",
    preview_mode=True
)

with ResumeSession(data_dir="resume_private", config=config) as session:
    # Generate all resumes
    session.generate_all(format="pdf")

    # Access specific resume
    resume = session.resume("my_resume")
    result = session.generate_resume(resume, format="html")
```

### `SessionConfig`

Configuration for ResumeSession.

```python
from simple_resume import SessionConfig

config = SessionConfig(
    default_template="resume_no_bars",
    preview_mode=False,
    auto_open=False
)
```

### `create_session`

Factory function for creating sessions.

```python
from simple_resume import create_session

session = create_session(
    data_dir="resume_private",
    default_template="resume_no_bars"
)

with session:
    session.generate_all(format="pdf")
```

---

## Result Types

### `GenerationResult`

Result of generating a single resume.

```python
from simple_resume import GenerationResult

result = GenerationResult(
    output_path=Path("output/resume.pdf"),
    format_type="pdf",
    metadata=GenerationMetadata(...)
)

# Check if generation succeeded
if result.exists:
    print(f"Generated: {result.output_path}")
```

**Properties:**
- `output_path: Path` - Path to generated file
- `format_type: str` - Format type ("pdf", "html", etc.)
- `metadata: GenerationMetadata` - Generation metadata
- `exists: bool` - Whether output file exists

### `BatchGenerationResult`

Result of batch generation operations.

```python
from simple_resume import BatchGenerationResult

result = BatchGenerationResult(
    successful=5,
    failed=0,
    skipped=1,
    errors={},
    results={...}
)

print(f"Success: {result.successful}")
print(f"Failed: {result.failed}")
```

**Properties:**
- `successful: int` - Count of successful generations
- `failed: int` - Count of failed generations
- `skipped: int` - Count of skipped generations
- `errors: dict[str, Exception]` - Error details per resume
- `results: dict[str, GenerationResult]` - Individual results

### `GenerationMetadata`

Metadata about a generation operation.

```python
from simple_resume import GenerationMetadata

metadata = GenerationMetadata(
    format_type="pdf",
    template_name="resume_no_bars",
    generation_time=1.23,
    file_size=45678,
    resume_name="my_resume",
    palette_info={...}
)
```

---

## Shell I/O Functions

These functions are exported from `simple_resume.shell.resume_extensions` and provide I/O operations for Resume objects.

### `to_pdf`

Generate PDF from a Resume.

```python
from simple_resume import Resume, to_pdf

resume = Resume.read_yaml("resume.yaml")
result = to_pdf(resume, output_path="output/resume.pdf", open_after=False)
```

**Parameters:**
- `resume: Resume` - The Resume instance
- `output_path: Path | str | None` - Optional output path
- `open_after: bool` - Whether to open after generation
- `strategy: PdfGenerationStrategy | None` - Optional custom strategy

**Returns:** `GenerationResult`

### `to_html`

Generate HTML from a Resume.

```python
from simple_resume import Resume, to_html

resume = Resume.read_yaml("resume.yaml")
result = to_html(resume, output_path="output/resume.html", open_after=False)
```

**Parameters:**
- `resume: Resume` - The Resume instance
- `output_path: Path | str | None` - Optional output path
- `open_after: bool` - Whether to open after generation
- `browser: str | None` - Optional browser command

**Returns:** `GenerationResult`

### `to_markdown`

Generate intermediate Markdown from a Resume.

```python
from simple_resume import Resume, to_markdown

resume = Resume.read_yaml("resume.yaml")
result = to_markdown(resume, output_path="output/resume.md")
```

**Returns:** `GenerationResult`

### `to_tex`

Generate intermediate LaTeX from a Resume.

```python
from simple_resume import Resume, to_tex

resume = Resume.read_yaml("resume.yaml")
result = to_tex(resume, output_path="output/resume.tex")
```

**Returns:** `GenerationResult`

### `render_markdown_file`

Render an existing Markdown file to HTML.

```python
from simple_resume import render_markdown_file

result = render_markdown_file(
    "output/resume.md",
    output_path="output/resume.html",
    open_after=False
)
```

**Returns:** `GenerationResult`

### `render_tex_file`

Render an existing LaTeX file to PDF.

```python
from simple_resume import render_tex_file

result = render_tex_file(
    "output/resume.tex",
    output_path="output/resume.pdf",
    open_after=False
)
```

**Returns:** `GenerationResult`

### `generate`

Shell-layer dispatcher for Resume generation.

```python
from simple_resume import Resume, OutputFormat, generate as shell_generate

resume = Resume.read_yaml("resume.yaml")
result = shell_generate(resume, format_type=OutputFormat.PDF)
```

**Parameters:**
- `resume: Resume` - The Resume instance
- `format_type: OutputFormat | str` - Output format
- `output_path: Path | str | None` - Optional output path
- `open_after: bool` - Whether to open after generation

**Returns:** `GenerationResult`

---

## Type Hints

All public API functions include type hints. For IDE autocomplete support, ensure:

```bash
# With uv (recommended)
uv add simple-resume

# Or with type stubs (future)
pip install simple-resume
```

---

## Version Information

```python
import simple_resume

print(simple_resume.__version__)  # "0.1.7"
```

---

## Related Documentation

- [Architecture Guide](Architecture-Guide.md) - FCIS architecture details
- [ADR-003: API Surface Design](architecture/ADR003-api-surface-design.md) - API design decisions
- [Usage Guide](Usage-Guide.md) - User-facing usage documentation
- [Development Guide](Development-Guide.md) - Contributing guidelines
