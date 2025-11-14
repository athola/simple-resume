# Architecture Guide: Functional Core, Imperative Shell

**Status:** In Progress (65% adherence, target 90%+)
**Last Updated:** 2025-11-14
**Related:** [ADR002](architecture/ADR002-functional-core-imperative-shell.md), [Refactoring Plan](../CORE_REFACTOR_PLAN.md)

## Overview

simple-resume uses a **Functional Core, Imperative Shell** architectural pattern. The goal is to isolate business logic from side effects (like file I/O or network requests).

The "core" contains pure, deterministic functions that can be tested without mocks. The "shell" handles all I/O and orchestrates calls to the core. This separation makes the codebase easier to maintain and test. For example, all core logic can be tested in memory, leading to extremely fast test runs.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / API Layer                      │
│         (User interface, argument parsing)              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Imperative Shell                       │
│         (I/O, orchestration, side effects)              │
│  ┌────────────────────────────────────────────────┐     │
│  │ shell/generation.py        - File I/O          │     │
│  │ shell/resume_loaders.py    - YAML loading      │     │
│  │ shell/pdf_operations.py    - PDF writing       │     │
│  │ shell/palette_fetching.py  - Network calls     │     │
│  │ shell/rendering_operations.py - External deps  │     │
│  └────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Data structures only (no I/O)
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Functional Core                       │
│           (Pure logic, deterministic)                   │
│  ┌────────────────────────────────────────────────┐     │
│  │ core/plan.py             - Validation          │     │
│  │ core/colors.py           - Color math          │     │
│  │ core/hydration_core.py   - Data transformation │     │
│  │ core/resume.py           - Resume domain model │     │
│  │ core/strategies.py       - Generation strategy │     │
│  │ core/pdf_generation.py   - PDF planning        │     │
│  │ core/html_generation.py  - HTML assembly       │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Import Rules

### ✅ ALLOWED

| From Layer | To Layer | Why |
|------------|----------|-----|
| Shell → Core | ✓ | Shell orchestrates core logic |
| Shell → External libs | ✓ | Shell manages I/O dependencies |
| Core → Core | ✓ | Core modules can compose |
| CLI → Shell | ✓ | CLI delegates to shell operations |
| CLI → Core | ✓ | CLI can use core types/models |

### ❌ FORBIDDEN

| From Layer | To Layer | Why |
|------------|----------|-----|
| Core → Shell | ✗ | Creates circular dependencies |
| Core → I/O libs | ✗ | Makes core impure and untestable |
| Core → Network | ✗ | Side effects belong in shell |
| Core → Filesystem | ✗ | File operations belong in shell |
| Core → subprocess | ✗ | External process calls belong in shell |

### Forbidden I/O Libraries in Core

Core modules **must not** import:
- `weasyprint` - PDF rendering (use shell)
- `yaml` - File parsing (use shell)
- `requests` / `urllib` - Network calls (use shell)
- `subprocess` - Process execution (use shell)
- `open()` - File operations (use shell)

### Special Cases

**file_operations.py** - Read-only file queries (e.g., `Path.glob()`) are acceptable as boundary cases. These don't mutate state and are used for discovery.

**Dependency Injection** - Core can accept callables/protocols that perform I/O, but must not instantiate them:

```python
# ✅ GOOD - Core accepts injected dependency
def hydrate_resume_structure(
    source_yaml: dict[str, Any],
    *,
    render_markdown_fn: Callable[[dict], dict],  # Injected!
) -> dict[str, Any]:
    return render_markdown_fn(source_yaml)

# ✗ BAD - Core imports and calls I/O directly
from ..utils.io import read_yaml_file

def hydrate_resume_structure(filename: str) -> dict[str, Any]:
    data = read_yaml_file(filename)  # I/O in core!
```

## Design Patterns

### 1. Pure Functions in Core

Core functions should be deterministic - same input always produces same output.

**Example:**

```python
# core/colors.py - Pure color calculation
def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    lum1 = relative_luminance(rgb1)
    lum2 = relative_luminance(rgb2)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)
```

**Characteristics:**
- No I/O operations
- No external state
- No side effects
- Easy to test
- Fast execution

### 2. Dependency Injection in Core

When core needs external operations, accept them as parameters.

**Example:**

```python
# core/hydration_core.py
NormalizeConfigFn = Callable[[dict, str], tuple[dict, dict | None]]
RenderMarkdownFn = Callable[[dict], dict]

def hydrate_resume_structure(
    source_yaml: dict[str, Any],
    *,
    normalize_config_fn: NormalizeConfigFn,  # Injected
    render_markdown_fn: RenderMarkdownFn,    # Injected
) -> dict[str, Any]:
    """Pure transformation with injected dependencies."""
    processed = copy.deepcopy(source_yaml)

    # Use injected functions
    config, meta = normalize_config_fn(processed["config"], "")
    processed["config"] = config

    return render_markdown_fn(processed)
```

**Shell provides implementations:**

```python
# shell/generation.py
from ..core.hydration_core import hydrate_resume_structure
from ..core.config_core import normalize_config
from ..utilities import render_markdown_content

result = hydrate_resume_structure(
    source_yaml,
    normalize_config_fn=normalize_config,  # Real I/O impl
    render_markdown_fn=render_markdown_content,
)
```

### 3. Request/Response Pattern

For complex operations, core returns a "plan" or "request" object; shell executes it.

**Example:**

```python
# core/generation_plans.py
@dataclass(frozen=True)
class PdfGenerationPlan:
    """Pure plan for PDF generation - no I/O."""
    html_content: str
    css_rules: str
    output_path: Path
    page_size: tuple[float, float]

# core/pdf_generation.py
def prepare_pdf_generation(...) -> PdfGenerationPlan:
    """Generate plan - perform no I/O."""
    html = render_template(...)
    css = compile_styles(...)

    return PdfGenerationPlan(
        html_content=html,
        css_rules=css,
        output_path=output_path,
        page_size=(width, height),
    )

# shell/pdf_operations.py
def execute_pdf_generation(plan: PdfGenerationPlan) -> GenerationResult:
    """Execute plan - perform I/O."""
    from weasyprint import HTML, CSS  # I/O library in shell

    plan.output_path.parent.mkdir(parents=True, exist_ok=True)

    html_doc = HTML(string=plan.html_content)
    css_doc = CSS(string=plan.css_rules)
    html_doc.write_pdf(str(plan.output_path), stylesheets=[css_doc])

    return GenerationResult(success=True, output_path=plan.output_path)
```

### 4. Protocol-Based Abstraction

Use protocols to define interfaces without coupling to implementations.

**Example:**

```python
# shell/generation.py
from typing import Protocol

class PdfWriter(Protocol):
    """Protocol for PDF writing - enables testing."""
    def write_pdf(self, plan: PdfGenerationPlan) -> GenerationResult: ...

class WeasyPrintWriter:
    """Production implementation."""
    def write_pdf(self, plan: PdfGenerationPlan) -> GenerationResult:
        # ... actual I/O ...
        pass

# Dependency injection container
@dataclass(frozen=True)
class GenerationDeps:
    pdf_writer: PdfWriter  # Protocol, not concrete type
    html_writer: HtmlWriter
    logger: Logger
    filesystem: FileSystem

# Tests provide mocks
class MockPdfWriter:
    def write_pdf(self, plan: PdfGenerationPlan) -> GenerationResult:
        return GenerationResult(success=True)  # No real I/O
```

### 5. Effect System (Advanced - Optional)

For maximum purity, core can return effect objects that shell interprets.

**Example:**

```python
# core/effects.py
@dataclass(frozen=True)
class Effect:
    """Base class for side effects."""
    pass

@dataclass(frozen=True)
class WriteFile(Effect):
    path: Path
    content: str

@dataclass(frozen=True)
class MakeDirectory(Effect):
    path: Path

# core/html_generation.py
def generate_html_effects(...) -> list[Effect]:
    """Return effects to execute - no I/O."""
    return [
        MakeDirectory(output_path.parent),
        WriteFile(output_path, html_content),
    ]

# shell/effect_executor.py
def execute_effects(effects: list[Effect]) -> None:
    """Interpret and execute effects."""
    for effect in effects:
        match effect:
            case WriteFile(path, content):
                path.write_text(content)
            case MakeDirectory(path):
                path.mkdir(parents=True, exist_ok=True)
```

## Testing Strategy

### Core Tests (Unit Tests)

Core tests are fast, deterministic, and require no mocking.

```python
# tests/unit/core/test_colors.py
def test_calculate_contrast_ratio():
    """Test pure color calculation."""
    # Arrange
    black = "#000000"
    white = "#FFFFFF"

    # Act
    ratio = calculate_contrast_ratio(black, white)

    # Assert
    assert ratio == 21.0  # WCAG maximum contrast

# No mocking needed!
# No I/O!
# Runs in microseconds!
```

**Characteristics:**
- No `@mock.patch` needed
- No file fixtures required
- No network stubs
- Parallel execution safe
- Fast (<1s for entire core suite)

### Shell Tests (Integration Tests)

Shell tests use dependency injection to isolate I/O.

```python
# tests/unit/shell/test_generation.py
class MockFileSystem:
    """Mock filesystem - no real I/O."""
    def __init__(self):
        self.written_files: dict[Path, str] = {}

    def write_file(self, path: Path, content: str) -> None:
        self.written_files[path] = content  # In-memory only

def test_generate_pdf_writes_file():
    """Test shell orchestration with mocks."""
    # Arrange
    mock_fs = MockFileSystem()
    mock_pdf_writer = MockPdfWriter()

    deps = GenerationDeps(
        pdf_writer=mock_pdf_writer,
        filesystem=mock_fs,
    )

    generator = ResumeGenerator(deps)

    # Act
    result = generator.generate_pdf(...)

    # Assert
    assert result.success
    assert output_path in mock_fs.written_files
```

**Characteristics:**
- Protocol-based mocks
- No real filesystem/network access
- Verify orchestration logic
- Test error handling

## Common Anti-Patterns

### ❌ Anti-Pattern 1: I/O in Core

```python
# core/pdf_generation.py - BAD!
def generate_pdf(...):
    output_path.parent.mkdir(parents=True, exist_ok=True)  # I/O!
    html_doc.write_pdf(str(output_path))  # I/O!
```

**Fix:** Return a plan; let shell execute it.

### ❌ Anti-Pattern 2: Core Importing Shell

```python
# core/strategies.py - BAD!
from ..shell.rendering_operations import generate_pdf
```

**Fix:** Use dependency injection.

### ❌ Anti-Pattern 3: Network Calls in Core

```python
# core/config_core.py - BAD!
client = ColourLoversClient()
palettes = client.fetch(...)  # Network I/O!
```

**Fix:** Return a fetch request; let shell execute it.

### ❌ Anti-Pattern 4: Shell Duplicating Logic

```python
# shell/generation.py - BAD!
def generate_resume(self, config):
    # Don't duplicate validation logic here!
    if config["page_width"] < 50:  # Logic should be in core
        raise ValueError("...")
```

**Fix:** Delegate all business logic to core.

### ❌ Anti-Pattern 5: Hidden Side Effects

```python
# core/utilities.py - BAD!
def process_config(config_path: str):
    with open(config_path) as f:  # Hidden I/O!
        data = yaml.load(f)
    return validate(data)
```

**Fix:** Accept pre-loaded data, not file paths.

## Refactoring Checklist

When refactoring a module to follow this pattern:

### For Core Modules

- [ ] No `import weasyprint`, `import yaml`, `import requests`
- [ ] No `from ..shell import ...`
- [ ] No `.write_text()`, `.read_text()`, `.mkdir()`, `.unlink()`
- [ ] No `open()`, `subprocess.run()`, network calls
- [ ] Functions accept data, not file paths
- [ ] Functions return data or plans, not None
- [ ] All external operations injected as parameters
- [ ] Type hints on all public functions
- [ ] Deterministic - same input = same output

### For Shell Modules

- [ ] Delegates all logic to core
- [ ] Performs I/O operations
- [ ] Handles errors and retries
- [ ] Manages external dependencies
- [ ] Uses dependency injection for testability
- [ ] Documents what I/O it performs
- [ ] Provides protocol interfaces

## Migration Guide

See [Migration Guide](Migration-Guide-Modernization.md) for step-by-step instructions on migrating existing code to this architecture.

## Enforcement

### Automated Tests

Architectural tests run on every commit and PR:

```bash
pytest tests/architecture/test_layer_separation.py
```

These tests enforce:
- No I/O library imports in core
- No shell imports in core
- No file operations in core
- No circular dependencies

### Pre-commit Hooks

Pre-commit hooks prevent violations before commit:

```bash
# .pre-commit-config.yaml
- id: architecture-tests
  entry: uv run pytest tests/architecture/
```

### CI/CD Gates

GitHub Actions run architectural tests on all PRs. PRs cannot merge if architectural tests fail.

## Current Status

### Compliant Modules (90-100% Pure)

- ✅ `core/plan.py` - Pure validation
- ✅ `core/colors.py` - Pure color math
- ✅ `core/color_service.py` - Pure color decisions
- ✅ `core/hydration_core.py` - Pure transformation with DI
- ✅ `shell/generation.py` - Excellent DI pattern

### Modules Under Refactoring

- ⚠️ `core/pdf_generation.py` - Removing file I/O (Phase 2)
- ⚠️ `core/html_generation.py` - Removing file I/O (Phase 2)
- ⚠️ `core/resume.py` - Moving I/O to shell (Phase 3)
- ⚠️ `core/config_core.py` - Removing network calls (Phase 4)
- ⚠️ `core/strategies.py` - Removing shell imports (Phase 2)

### Progress Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Core purity | 65% | 90%+ |
| P0 violations | 6 | 0 |
| Test coverage | 85% | 90%+ |
| Core test speed | <1s | <1s ✓ |

## Resources

- [ADR002: Functional Core, Imperative Shell](architecture/ADR002-functional-core-imperative-shell.md)
- [Functional Core Shell Inventory](architecture/Functional-Core-Shell-Inventory.md)
- [Refactoring Plan](../CORE_REFACTOR_PLAN.md)
- [Migration Guide](Migration-Guide-Modernization.md)
- [Gary Bernhardt - Boundaries (video)](https://www.destroyallsoftware.com/talks/boundaries)
- [Mark Seemann - Functional Architecture](https://blog.ploeh.dk/2016/03/18/functional-architecture-is-ports-and-adapters/)

## Questions & Support

For questions about this architecture:
1. Review the ADR002 document for rationale
2. Check the refactoring plan for implementation timeline
3. Ask in architecture review sessions
4. Reference this guide in code reviews

---

**Maintained by:** Architecture team
**Last updated:** 2025-11-14
**Version:** 1.0
