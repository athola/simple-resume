# API Stability Policy

**Version:** 1.0
**Effective:** 2025-01-03
**Applies to:** simple-resume ≥ 0.1.0

---

## Overview

This document defines the stability guarantees for the simple-resume public API. It follows semantic versioning principles and is inspired by established libraries like [pandas](https://pandas.pydata.org/docs/development/policies.html) and [Azure SDK](https://azure.github.io/azure-sdk/general_design.html).

---

## Stability Levels

### ✅ Stable (Public API)

The symbols listed in `simple_resume.__all__` are **stable** and follow semantic versioning:

```python
import simple_resume

# All exports in __all__ are stable
stable_exports = simple_resume.__all__
# 32 stable exports as of v0.1.7
```

**Guarantees:**
- ✅ Backward compatibility within major versions
- ✅ Deprecation warnings before removal (2 minor versions minimum)
- ✅ Documented migration paths for breaking changes
- ✅ Type hints for IDE autocomplete

**Example Stable APIs:**
- `simple_resume.Resume`
- `simple_resume.generate_pdf`
- `simple_resume.ResumeSession`
- All exceptions (`ValidationError`, `GenerationError`, etc.)

### ⚠️ Internal (May Change)

Modules under `simple_resume.core.*` and `simple_resume.shell.*` are **internal** and may change without notice:

```python
# ⚠️ Not guaranteed to be stable
from simple_resume.core.resume import Resume  # Works but may break
from simple_resume.shell.generate import generate_pdf  # May change signatures
```

**Why Internal?**
- Core modules contain implementation details
- Shell modules adapt to external dependencies
- We reserve the right to refactor for performance/maintainability

**Use Internal APIs When:**
- You need advanced customization
- You're extending the library
- You're willing to track upstream changes

### 🔄 Deprecated

Previously stable APIs scheduled for removal:

```python
# Deprecated in v0.1.7, removal in v0.3.0
from simple_resume import old_function  # Raises DeprecationWarning
```

**Deprecation Process:**
1. Mark as deprecated with `DeprecationWarning`
2. Document alternative approach
3. Maintain for 2 minor versions minimum
4. Remove in next major version

---

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (0.x.0): Breaking changes to public API
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

### Version Compatibility Matrix

| Your Version | simple-resume 0.1.x | simple-resume 0.2.x | simple-resume 1.0.x |
|--------------|-------------------|-------------------|-------------------|
| 0.1.0        | ✅ Compatible      | ⚠️ May break       | ❌ Breaks         |
| 0.1.7        | ✅ Current         | ⚠️ May break       | ❌ Breaks         |
| 0.2.0        | ❌ Breaks         | ✅ Compatible      | ⚠️ May break       |
| 1.0.0        | ❌ Breaks         | ❌ Breaks         | ✅ Compatible      |

---

## Public API Surface

### Stable Exports (v0.1.7)

All 29 symbols in `simple_resume.__all__`:

```python
# Core models (data only)
"Resume", "ResumeConfig", "RenderPlan", "ValidationResult"  # 4 exports

# Exceptions
"SimpleResumeError", "ValidationError", "ConfigurationError",
"TemplateError", "GenerationError", "PaletteError",
"FileSystemError", "SessionError"  # 8 exports

# Results & sessions
"GenerationResult", "GenerationMetadata", "BatchGenerationResult",
"ResumeSession", "SessionConfig", "create_session"  # 6 exports

# Generation primitives
"GenerationConfig"  # 1 export
"generate_pdf", "generate_html", "generate_all", "generate_resume"  # 4 exports

# Shell layer I/O functions
"to_pdf", "to_html", "resume_generate"  # 3 exports

# Convenience helpers
"generate", "preview"  # 2 exports
```

### Verifying API Membership

```python
import simple_resume

# Check if a symbol is part of the stable API
def is_stable_api(symbol: str) -> bool:
    return symbol in simple_resume.__all__

print(is_stable_api("Resume"))  # True
print(is_stable_api("generate_pdf"))  # True
print(is_stable_api("core"))  # False (internal module)
```

---

## Breaking Changes Policy

A **breaking change** is any modification that could break existing user code:

### Examples of Breaking Changes

- ❌ Removing a stable export
- ❌ Renaming a stable export
- ❌ Changing a function signature (required parameters)
- ❌ Changing a return type incompatibly
- ❌ Removing a method from a stable class

### Examples of Non-Breaking Changes

- ✅ Adding new exports
- ✅ Adding optional parameters with defaults
- ✅ Adding new methods to classes
- ✅ Extending return types (covariance)
- ✅ Performance improvements
- ✅ Bug fixes that preserve behavior

### Breaking Change Process

1. **Announce**: Document in changelog 2 minor versions ahead
2. **Deprecate**: Add `DeprecationWarning` to old API
3. **Migrate**: Provide migration guide and new API
4. **Remove**: Remove in next major version

```python
# Example deprecation (v0.1.7)
import warnings

def old_generate(resume, format):
    warnings.warn(
        "old_generate is deprecated and will be removed in v0.3.0. "
        "Use 'generate' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return generate(resume, format)
```

---

## Extension Points

While `simple_resume.core.*` and `simple_resume.shell.*` are internal, some extension points are designed for customization:

### Stable Extension Points

1. **Templates**: Custom Jinja2 templates (documented in Usage Guide)
2. **Palettes**: Custom color palettes (documented in Color Schemes)
3. **Importers**: Custom data importers (via `simple_resume.core.importers`)
4. **Strategies**: PDF generation strategies (via `PdfGenerationStrategy` protocol)

### Extension Best Practices

```python
# ✅ Good: Use stable APIs when extending
from simple_resume import Resume
from simple_resume.core.protocols import PdfGenerationStrategy

class CustomPdfStrategy(PdfGenerationStrategy):
    def generate(self, render_plan, output_path, ...):
        # Custom implementation
        pass

# ⚠️ Avoid: Depending on internal implementation details
from simple_resume.shell.render.latex import _internal_function  # May break
```

---

## Monitoring and Enforcement

### Automated Checks

We use automated checks to enforce API stability:

1. **API Surface Scanner**: Ensures `__all__` is up-to-date
2. **Type Hint Validation**: Ensures public APIs have type hints
3. **Deprecation Scanner**: Ensures deprecated APIs emit warnings
4. **Documentation Sync**: Ensures API reference matches code

### Reporting Issues

If you encounter a breaking change not documented in the changelog:

1. Check the [API Reference](API-Reference.md) for correct usage
2. Review the [Migration Guide](Migration-Guide.md) for migration steps
3. [Open an issue](https://github.com/athola/simple-resume/issues) with details

---

## Future Stability Guarantees

### Planned Stable Additions (v0.2.0)

We are considering promoting these to stable status:

- `simple_resume.core.colors` - Color utilities (WCAG calculations)
- `simple_resume.core.importers` - Data importers
- `simple_resume.core.protocols` - Extension protocols

### Experimental APIs

 APIs marked as **experimental** may change in any release:

- `simple_resume.shell.generate.core` - Advanced generation options
- `simple_resume.shell.strategies` - Custom generation strategies

Experimental APIs are not in `__all__` and should be used with caution.

---

## Comparison with Other Libraries

| Library | Stability Policy | Public API | Internal |
|---------|------------------|------------|----------|
| **simple-resume** | `__all__` only | ✅ Stable | ⚠️ May change |
| **pandas** | `pandas.api.*` | ✅ Stable | ⚠️ May change |
| **requests** | Top-level only | ✅ Stable | ⚠️ May change |
| **Azure SDK** | Documented guidelines | ✅ Stable | ⚠️ May change |

Our policy aligns with established Python libraries while being simpler for our scope.

---

## Related Documentation

- [API Reference](API-Reference.md) - Complete API documentation
- [ADR-003: API Surface Design](architecture/ADR003-api-surface-design.md) - Design decisions
- [Migration Guide](Migration-Guide.md) - Version migration instructions
- [Contributing](Contributing.md) - Contribution guidelines

---

## Changelog

### v0.1.7 (2025-01-03)
- ✅ Added API Stability Policy
- ✅ Created API Reference documentation
- ✅ Fixed version mismatch between `__init__.py` and `pyproject.toml`

### v0.1.6
- ✅ Established `__all__` exports as stable public API
- ✅ Added lazy-loading for performance

### v0.1.0
- ✅ Initial public API definition
- ✅ FCIS architecture implementation
