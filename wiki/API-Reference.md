# API Reference

**Version:** 0.2.2
**Last Updated:** 2026-01-22
**Stability:** Public API exports follow semantic versioning guarantees

---

## Table of Contents

- [Stability Contract](#stability-contract)
- [Core Models](#core-models)
- [Exceptions](#exceptions)
- [Generation Functions](#generation-functions)
- [ATS Scoring](#ats-scoring) ⭐ NEW
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

## ATS Scoring

Score resumes against job descriptions using multiple NLP algorithms in a tournament-style approach.

### `score_resume`

Convenience function to score a resume against a job description using the default tournament.

```python
from simple_resume import score_resume

result = score_resume(
    resume_text="Senior Python Developer with 5 years experience...",
    job_description="We are looking for a Senior Engineer..."
)

print(f"Match score: {result.overall_score * 100:.1f}%")
print(f"Algorithms used: {result.metadata['scorer_names']}")
```

**Parameters:**
- `resume_text: str` - Full resume text
- `job_description: str` - Full job description text
- `custom_scorers: list[BaseScorer] | None` - Optional custom scoring algorithms

**Returns:** `TournamentResult`

### `ATSTournament`

Multi-algorithm tournament runner for comprehensive resume-job matching.

```python
from simple_resume import ATSTournament, TFIDFScorer, JaccardScorer

# Custom tournament with specific weights
tournament = ATSTournament(scorers=[
    TFIDFScorer(weight=0.5),
    JaccardScorer(weight=0.5),
])

result = tournament.score(resume_text, job_description)
```

**Parameters:**
- `scorers: list[BaseScorer] | None` - List of scoring algorithms (defaults to TF-IDF, Jaccard, Keyword)

**Methods:**
- `score(resume_text, job_description, **kwargs) -> TournamentResult` - Score resume against job
- `get_top_matches(resumes, job_description, top_n=10) -> list` - Rank multiple resumes

### `TFIDFScorer`

TF-IDF + Cosine Similarity scorer for statistical keyword analysis.

```python
from simple_resume import TFIDFScorer

scorer = TFIDFScorer(
    weight=1.0,
    max_features=1000,
    ngram_range=(1, 2)  # Unigrams + bigrams
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Fast, interpretable, good for exact keyword matching
**Cons:** Misses semantic meaning, no context understanding

### `JaccardScorer`

Jaccard similarity + N-gram overlap scorer for phrase matching.

```python
from simple_resume import JaccardScorer

scorer = JaccardScorer(
    weight=1.0,
    ngram_range=(1, 3),  # Unigrams to trigrams
    case_sensitive=False
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Simple, interpretable, good for exact phrase matching
**Cons:** Limited to surface-level matching, misses semantic variations

### `KeywordScorer`

Exact keyword match scorer with fuzzy tolerance.

```python
from simple_resume import KeywordScorer

scorer = KeywordScorer(
    weight=1.0,
    fuzzy_threshold=0.85,
    extract_keywords=True
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Fast, simple, good for hard requirements
**Cons:** Misses semantic variations, vulnerable to keyword stuffing

### `BERTScorer` (Optional)

Semantic similarity scorer using sentence-transformers. Requires the `bert` extra.

```bash
# Install with bert extra
uv add simple-resume[bert]
pip install simple-resume[bert]
```

```python
from simple_resume import BERTScorer

# BERTScorer is None if sentence-transformers not installed
if BERTScorer is not None:
    scorer = BERTScorer(
        weight=1.0,
        model_name="all-MiniLM-L6-v2"  # Default model
    )
    result = scorer.score(resume_text, job_description)
```

**Pros:** Understands semantic meaning, handles synonyms and paraphrasing
**Cons:** Slower than statistical methods, requires GPU for best performance

### `ScorerName` and `ScorerSelection`

Enumerations for algorithm identification.

```python
from simple_resume import ScorerName, ScorerSelection

# Algorithm names (internal identifiers)
ScorerName.TFIDF_COSINE      # "tfidf_cosine"
ScorerName.JACCARD_NGRAM     # "jaccard_ngram"
ScorerName.KEYWORD_EXACT     # "keyword_exact"
ScorerName.BERT_SEMANTIC     # "bert_semantic"

# Selection shortcuts (user-facing)
ScorerSelection.TFIDF        # "tfidf"
ScorerSelection.JACCARD      # "jaccard"
ScorerSelection.KEYWORD      # "keyword"
ScorerSelection.BERT         # "bert"
```

### `BaseScorer`

Abstract base class for implementing custom scoring algorithms.

```python
from simple_resume import BaseScorer, ScorerResult

class CustomScorer(BaseScorer):
    def score(self, resume_text, job_description, **kwargs):
        # Your scoring logic here
        score = 0.75  # Example score
        return ScorerResult(
            name="custom",
            score=score,
            weight=self.weight,
            details={"custom_metric": 123}
        )
```

### `TournamentResult`

Result from running multiple scoring algorithms.

```python
from simple_resume import TournamentResult

result.overall_score  # Final weighted average (0-1)
result.algorithm_results  # List of individual ScorerResult
result.component_breakdown  # Scores by rubric component
result.metadata  # Tournament metadata
result.to_dict()  # Convert to dictionary
```

### `ScorerResult`

Result from an individual scoring algorithm.

```python
from simple_resume import ScorerResult

result.name  # Algorithm name
result.score  # Raw score (0-1)
result.weighted_score  # Score × weight
result.details  # Algorithm-specific details
result.component_scores  # Component breakdown
result.to_dict()  # Convert to dictionary
```

### `ExtractedEntities`

Structured entities extracted from resume or job description.

```python
from simple_resume import EntityExtractor

extractor = EntityExtractor(
    extract_keywords=True,
    custom_skills=["Golang", "Rust"]
)
entities = extractor.extract(text)

entities.skills  # List of skills
entities.experience_years  # Total years
entities.degrees  # List of degrees
entities.certifications  # List of certifications
entities.keywords  # TF-IDF keywords (word, score)
entities.to_dict()  # Convert to dictionary
```

### `ParsedDocument`

Lazy-evaluated parsed document for efficient entity extraction. Implements the parse-once architecture.

```python
from simple_resume import parse, ParsedDocument

# Create via parse() function (recommended)
doc = parse("  Resume text   here...  ")

# Lazy properties (computed once on first access)
doc.raw_text         # Original input
doc.normalized_text  # Whitespace-normalized
doc.lowercase_text   # Lowercase for case-insensitive matching
doc.lines            # Non-empty lines
doc.sentences        # Sentence-split text
doc.word_tokens      # Alphabetic tokens

# Section finding helper
skills_section = doc.find_section(r"Skills|Technologies")
```

**Properties:** Each property is computed once and cached via `@cached_property`.

### `Degree`

Structured representation of an educational degree.

```python
from simple_resume import Degree

degree = Degree(
    type="Bachelor",
    school="MIT",
    field="Computer Science"
)

degree.to_dict()  # {"type": "Bachelor", "school": "MIT", "field": "Computer Science"}
```

### `EntityExtractor`

Extract structured entities from unstructured text. Accepts both raw strings and `ParsedDocument` objects.

```python
from simple_resume import EntityExtractor, extract_entities, parse

# Class-based usage with string
extractor = EntityExtractor(extract_keywords=True)
entities = extractor.extract(resume_text)

# Class-based with ParsedDocument (efficient for multiple extractions)
doc = parse(resume_text)
entities = extractor.extract(doc)

# Function-based usage
entities = extract_entities(resume_text, custom_skills=["Kubernetes"])
```

### `ATSReportGenerator`

Generate human-readable reports from tournament results.

```python
from simple_resume import ATSReportGenerator
from pathlib import Path

report_gen = ATSReportGenerator(
    result=tournament_result,
    resume_file="my_resume.yaml",
    job_file="job_description.txt",
    job_url="https://company.com/jobs/123"
)

# Generate report content
yaml_report = report_gen.generate_yaml()
json_report = report_gen.generate_json(indent=2)

# Save to file (shell layer responsibility)
Path("output/ats_report.yaml").write_text(yaml_report)
```

**Output includes:**
- Overall score with status label
- Algorithm breakdown with individual scores
- Component scores (experience, skills, semantic, keywords)
- Recommendations for improvement

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

print(simple_resume.__version__)  # "0.2.2"
```

---

## Related Documentation

- [Architecture Guide](Architecture-Guide.md) - FCIS architecture details
- [ADR-003: API Surface Design](architecture/ADR003-api-surface-design.md) - API design decisions
- [Usage Guide](Usage-Guide.md) - User-facing usage documentation
- [Development Guide](Development-Guide.md) - Contributing guidelines
