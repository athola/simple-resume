![Simple-Resume preview screenshot](assets/preview.png)

_Generate polished PDF and HTML resumes from a single YAML file._

[![PyPI Downloads](https://img.shields.io/pypi/dm/simple-resume?style=flat-square)](https://pypi.org/project/simple-resume/)
[![MIT License](https://img.shields.io/github/license/athola/simple-resume?style=flat-square)](https://github.com/athola/simple-resume/blob/main/LICENSE)
[![Code Quality](https://github.com/athola/simple-resume/workflows/Code%20Quality/badge.svg)](https://github.com/athola/simple-resume/actions/workflows/code-quality.yml)
[![Linting](https://github.com/athola/simple-resume/workflows/Linting/badge.svg)](https://github.com/athola/simple-resume/actions/workflows/lint.yml)
[![Test Suite](https://github.com/athola/simple-resume/workflows/Test%20Suite/badge.svg)](https://github.com/athola/simple-resume/actions/workflows/test.yml)
[![Code Coverage](https://codecov.io/gh/athola/simple-resume/branch/main/graph/badge.svg)](https://codecov.io/gh/athola/simple-resume)
[![PyPI Version](https://img.shields.io/pypi/v/simple-resume.svg)](https://pypi.org/project/simple-resume/)

# simple-resume

A Python 3.10+ CLI and library for converting structured YAML
(or [JSON Resume][jsonresume]) into PDF, HTML, or LaTeX.
Templates and static assets ship with the package so you can render
without creating additional content.

## Why Simple-Resume

- Keep your resume version-controlled as plain YAML.
- Swap templates, palettes, and formats without rewriting content.
- Score resumes against job descriptions with built-in ATS algorithms.
- Pure-Python core with shell adapters; effects are testable and
  side-effect aware.
- Bundled HTML templates and static assets prevent "TemplateNotFound"
  errors in wheels and editable installs.

## Feature Comparison

| Feature | simple-resume | JSON Resume | HackMyResume | Resume.io |
|---------|---------------|-------------|--------------|-----------|
| Open Source | Yes | Yes | Yes | No |
| Data Format | YAML + JSON Resume | JSON | JSON/FRESH | Proprietary |
| Version Control | Git-friendly | Git-friendly | Git-friendly | Cloud-only |
| Local Processing | 100% private | 100% private | 100% private | Cloud storage |
| Template System | HTML + Jinja2 | JSON themes | Multiple formats | Web builder |
| LaTeX Support | Yes | No | No | No |
| Python API | Native | No | No | No |
| CLI Tools | Yes | Yes | Yes | No |
| Real-time Preview | HTML + auto-reload | No | No | Yes |
| ATS Scoring | Built-in (4 algorithms) | No | No | No |
| Custom Themes | Unlimited | Limited | Limited | Paid only |
| Color Palettes | Yes | No | Basic | Limited |

See [Detailed Comparison](wiki/Comparison.md) for full analysis.

## Installation

```bash
# With uv (recommended)
uv add simple-resume

# With pip
pip install simple-resume
```

**Platform requirements:** Python 3.10+ on Linux, macOS, or Windows.
PDF output uses WeasyPrint, which requires Cairo/Pango/GTK system
libraries (see [Usage Guide](wiki/Usage-Guide.md)).

## Quick Start

Create a YAML file in `resume_private/input/my_resume.yaml`:

> JSON Resume (`*.json` from [jsonresume.org][jsonresume]) is also
> supported — drop it into your `input/` folder and `simple-resume`
> auto-converts it at load time.
>
> Editor autocomplete is available via the JSON Schema at
> `src/simple_resume/shell/assets/static/schema.json`.

```yaml
template: resume_no_bars
full_name: Jane Doe
email: jane.doe@example.com
body:
  Experience:
    - title: Senior Engineer
      company: TechCorp
      start: 2022
      end: Present
      description: |
        - Lead microservices migration
        - Improved latency by 40%
```

Generate output:

```bash
uv run simple-resume generate --format pdf         # PDF
uv run simple-resume generate --format html --open # HTML + browser
```

Built-in templates: `resume_no_bars`, `resume_with_bars`,
`resume_modern`, `resume_professional`, `resume_creative`, `demo`.
Cover letters use the `cover` template.
See `src/simple_resume/shell/assets/templates/html/` for all templates.

## Python API

```python
from simple_resume import generate, preview

results = generate("resume_private/input/my_resume.yaml",
                   formats=["pdf", "html"])
print(results["pdf"].output_path)

# Browser preview with live reload
preview("resume_private/input/my_resume.yaml")
```

For batch operations:

```python
from simple_resume import ResumeSession

with ResumeSession(data_dir="resume_private") as session:
    session.generate_all(format="pdf")
```

See [API Reference](wiki/API-Reference.md) and
[API Stability Policy](wiki/API-Stability-Policy.md) for the full
public surface.

## ATS Resume Scoring

Score resumes against job descriptions using multiple NLP algorithms.

### CLI

```bash
# Single resume
uv run simple-resume screen resume.yaml job.txt

# Batch mode — rank all resumes in a directory
uv run simple-resume screen resumes/ job.txt --batch --top 5
```

### Python API

```python
from simple_resume import score_resume

result = score_resume(
    resume_text="Senior Python Developer with 5 years experience...",
    job_description="Looking for a Senior Python Engineer..."
)
print(f"Match score: {result.overall_score * 100:.1f}%")
```

### Scoring algorithms

- **TF-IDF + Cosine Similarity** — statistical term frequency analysis
- **Jaccard + N-gram** — set intersection and phrase overlap
- **Exact Keyword** — direct matching with fuzzy tolerance and
  skills taxonomy
- **BERT Semantic** — contextual embeddings via sentence-transformers
  (optional: `uv add simple-resume[bert]`)

The tournament system combines algorithms using weighted averages.
See [ATS API Reference](wiki/ATS-API-Reference.md) for the scoring API,
[ATS Scoring Rubric](wiki/ATS-Scoring-Rubric.md) for methodology, and
[Similarity Algorithm Evaluation](wiki/Similarity-Algorithm-Evaluation.md)
for benchmarks.

## Customization

- **Palettes**: `--palette "Professional Blue"` or
  `--palette path/to/palette.yaml`
- **Custom templates**: `--template custom.html` with
  `--templates-dir /path/to/templates`
- **LaTeX**: set `config.output_mode: latex` and compile with your TeX
  toolchain (see [Usage Guide](wiki/Usage-Guide.md#latex-output))
- **Color utilities**:
  `simple_resume.core.colors.get_contrasting_text_color` for
  accessibility checks

## Documentation

**Getting started:** [Getting Started](wiki/Getting-Started.md),
[Usage Guide](wiki/Usage-Guide.md),
[Workflows](wiki/Workflows.md),
[Path Handling](wiki/Path-Handling-Guide.md)

**API:** [API Reference](wiki/API-Reference.md),
[ATS API Reference](wiki/ATS-API-Reference.md),
[Shell Layer APIs](wiki/Shell-Layer-APIs.md),
[API Stability Policy](wiki/API-Stability-Policy.md)

**Architecture:** [Architecture Guide](wiki/Architecture-Guide.md),
[Lazy Loading](wiki/Lazy-Loading-Guide.md),
[Migration Guide](wiki/Migration-Guide.md)

**Design:** [Color Schemes](wiki/Color-Schemes.md),
[PDF Renderer Evaluation](wiki/PDF-Renderer-Evaluation.md)

**Samples:** `sample/` directory

## Development

```bash
git clone https://github.com/athola/simple-resume.git
cd simple-resume
uv sync --dev --extra utils   # or: pip install -e .[dev,utils]
```

Run checks before opening a PR:

```bash
make lint && make test         # or: make check-all validate
```

Releases are automated via GitHub Actions — tag with `v*` and push:

```bash
git tag v0.1.2 && git push origin v0.1.2
```

See [Development Guide](wiki/Development-Guide.md) and
[Contributing](wiki/Contributing.md) for full details.
Submit issues or ideas in
[GitHub Issues](https://github.com/athola/simple-resume/issues).

## Troubleshooting

- **TemplateNotFound**: confirm installation includes packaged assets;
  custom templates require `--templates-dir`.
- **PDF on Linux**: install system libs `cairo`, `pango`, `gdk-pixbuf`
  (WeasyPrint requirement).
- **PDF rendering errors**: `simple-resume` pins
  `pydyf>=0.10.0,<0.12.0` to avoid incompatible releases. Overriding
  this constraint may cause silent failures.
- **Case-variant `input/` directories**: `Input/`, `INPUT/`, etc. are
  detected automatically (v0.2.5+).

## License

MIT License. See [LICENSE](LICENSE).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=athola/simple-resume&type=date&legend=top-left)](https://www.star-history.com/#athola/simple-resume&type=date&legend=top-left)

[jsonresume]: https://jsonresume.org
