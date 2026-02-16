# Functional Core and Imperative Shell Inventory

This document inventories modules refactored to follow the "functional core, imperative shell" pattern.

## Current Module Structure

### Core Layer (`src/simple_resume/core/`)

Pure functions and data structures with no I/O operations.

| Module | Purpose | Purity Status |
| --- | --- | --- |
| `core/colors.py` | WCAG luminance/contrast calculations, ColorCalculationService | Pure |
| `core/config.py` | Configuration normalization and validation | Pure |
| `core/constants/` | Application constants (colors, files, layout) | Pure |
| `core/effects.py` | Effect types (WriteFile, MakeDirectory, etc.) | Pure |
| `core/exceptions.py` | Exception hierarchy | Pure |
| `core/file_operations.py` | Pure file path operations (no I/O) | Pure |
| `core/generate/html.py` | HTML generation planning | Pure |
| `core/generate/pdf.py` | PDF generation planning (Effect system) | Pure |
| `core/generate/plan.py` | Generation plan creation | Pure |
| `core/hydration.py` | Data hydration transformations | Pure |
| `core/latex/` | LaTeX rendering logic (context, conversion, escaping, etc.) | Pure |
| `core/markdown.py` | Markdown to HTML transformation | Pure |
| `core/models.py` | Data models (RenderPlan, ValidationResult, RenderMode) | Pure |
| `core/palettes/` | Palette resolution, generators, registry | Pure |
| `core/paths.py` | Path data structure | Pure |
| `core/render/` | Render request preparation; `plan.py` contains canonical render plan logic | Pure |
| `core/result.py` | GenerationResult and BatchGenerationResult (pure data) | Pure |
| `core/resume.py` | Resume class with dependency injection | Pure (late-bound I/O) |
| `core/skills.py` | Skills data transformations | Pure |
| `core/validation.py` | Configuration validation logic | Pure |
| `core/ats/base.py` | ATS scorer base classes and result types | Pure |
| `core/ats/bert.py` | BERT semantic similarity scorer | Pure (late-bound I/O) |
| `core/ats/constants.py` | ATS scoring constants and validation helpers | Pure |
| `core/ats/creative_terms.py` | Creative industry term mappings | Pure |
| `core/ats/entities.py` | Entity extraction from text | Pure |
| `core/ats/jaccard.py` | Jaccard + N-gram overlap scorer | Pure |
| `core/ats/keyword.py` | Keyword extraction and matching scorer | Pure |
| `core/ats/taxonomy.py` | Skill taxonomy and categorization | Pure |
| `core/ats/tfidf.py` | TF-IDF + Cosine similarity scorer | Pure |
| `core/ats/tournament.py` | Multi-algorithm tournament runner | Pure |
| `core/ats/reports.py` | ATS report generation | Pure |

### Shell Layer (`src/simple_resume/shell/`)

I/O operations, external dependencies, and orchestration.

| Module | Purpose | I/O Type |
| --- | --- | --- |
| `shell/cli/` | Command-line interface | User I/O, file I/O |
| `shell/config.py` | Configuration loading | File I/O |
| `shell/effect_executor.py` | Executes Effect objects from core | File I/O, subprocess |
| `shell/file_opener.py` | Platform-specific file opening | Subprocess, webbrowser |
| `shell/generate/core.py` | Generation orchestration | File I/O |
| `shell/generate/lazy.py` | Lazy loading utilities | Module loading |
| `shell/io_utils.py` | File system utilities | File I/O |
| `shell/palettes/fetch.py` | Remote palette fetching | Network I/O |
| `shell/palettes/loader.py` | Palette file loading | File I/O |
| `shell/palettes/remote.py` | ColourLovers API client | Network I/O |
| `shell/pdf_executor.py` | PDF generation execution | Subprocess |
| `shell/render/latex.py` | LaTeX compilation | Subprocess |
| `shell/render/operations.py` | HTML/PDF rendering operations | File I/O, weasyprint |
| `shell/runtime/content.py` | Content loading | File I/O |
| `shell/runtime/generate.py` | Generation runtime | File I/O |
| `shell/session/` | Session management | File I/O, state |
| `shell/strategies.py` | PDF generation strategies | I/O delegation |
| `shell/cli/_generation.py` | CLI generation helpers: format coercion, plan building | User I/O |
| `shell/cli/_screen.py` | ATS screening display and file-reading | User I/O, file I/O |
| `shell/service_locator.py` | Service registry for dependency injection | State |
| `shell/taxonomy_cache.py` | Taxonomy cache file I/O | File I/O |

## Key Architectural Patterns

### 1. Effect System

Core functions return Effect objects describing side effects:

```python
# core/effects.py
@dataclass(frozen=True)
class WriteFile(Effect):
    path: Path
    content: str | bytes

# shell/effect_executor.py
class EffectExecutor:
    def execute(self, effect: Effect) -> Any:
        if isinstance(effect, WriteFile):
            effect.path.write_text(effect.content)
```

### 2. Late-Bound Dependencies

Core modules use late binding to avoid import-time shell dependencies:

```python
# core/resume.py
def _get_pdf_strategy(mode: str) -> PdfGenerationStrategy:
    """Get the appropriate PDF generation strategy."""
    from simple_resume.shell.strategies import LatexStrategy, WeasyPrintStrategy

    if mode == "latex":
        return LatexStrategy()
    return WeasyPrintStrategy()
```

### 3. Protocol-Based Dependency Injection

Core defines protocols, shell provides implementations:

```python
# core/resume.py
class ContentLoader(Protocol):
    def load(self, name: str, paths: Paths | None, transform_markdown: bool) -> tuple[dict, dict]:
        ...

# Usage with injection for testing
Resume.read_yaml(name, content_loader=mock_loader)
```

### 4. Pure Result Objects

`GenerationResult` is a pure data class; I/O operations are in shell:

```python
# core/result.py - Pure data
@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    format_type: str
    metadata: GenerationMetadata | None = None

# shell/file_opener.py - I/O operations
def open_file(path: Path, format_type: str | None = None) -> bool:
    ...
```

## Known Violations (Tracked)

| File | Violation | Tracked In | Status |
| --- | --- | --- | --- |
| `core/generate/pdf.py` | Previously imported weasyprint | N/A | Fixed (Effect system) |
| `core/result.py` | Previously had subprocess | N/A | Fixed |
| `core/resume.py` | Previously imported shell at module level | N/A | Fixed (late binding) |

## Testing Strategy

### Core Tests
- Fast, deterministic, no mocks required
- Test pure functions with input/output assertions
- Located in `tests/unit/core/`

### Shell Tests
- Use dependency injection for isolation
- Mock external services (filesystem, network)
- Located in `tests/unit/shell/`

### Architecture Tests
- Enforce layer separation automatically
- Run on every commit: `pytest tests/architecture/`
- Detect forbidden imports, shell dependencies in core

## Next Steps

1. **Add architecture test for absolute imports**: Detect `from simple_resume.shell.*` in core
2. **Increase test coverage**: Target 85%+ for core modules
3. **Document API stability**: Mark public vs internal APIs
4. **Verify architecture tests**: Ensure test_layer_separation.py passes with updated structure

## Related Documentation

- [Architecture Guide](../Architecture-Guide.md)
- [ADR002: Functional Core, Imperative Shell](ADR002-functional-core-imperative-shell.md)
- [ADR003: API Surface Design](ADR003-api-surface-design.md)
- [Migration Guide](../Migration-Guide-Modernization.md)
