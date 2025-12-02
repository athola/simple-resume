# ADR-003: API Surface Design and Organization

## Status

Superseded by ADR-009 (FCIS Architecture) - Color utilities now in `simple_resume.core.colors`

Original: Accepted (2025-11-09)

## Context

The original API surface presented organizational issues:

1. Redundant wrapper functions adding no abstraction (`utilities.calculate_text_color()` wrapping `core.colors.get_contrasting_text_color()`)
2. Utility functions incorrectly exposed as `Resume` class methods (e.g., `Resume.calculate_text_color()`)
3. No clear public API namespace; users imported from internal `core.*` modules
4. Inconsistent function naming (`is_valid_color()` and `validate_color()` coexisting)

This violated established API design patterns from mature libraries (e.g., pandas, requests) and created a maintenance burden.

## Decision

### 1. Adopt Industry-Standard API Organization Patterns

After researching pandas and requests API design:

**pandas pattern:**

- Class methods: Operations on an object (`df.groupby()`, `df.plot()`)
- Top-level functions: Create/combine objects (`pd.read_csv()`, `pd.concat()`)
- `pandas.api.*` submodules: Specialized utilities (`pandas.api.types`, `pandas.api.extensions`)
- Core is PRIVATE: Users never import from `pandas.core.*`

**requests pattern:**

- Session class methods: Stateful operations only
- Utility modules: Separate modules for utilities (`requests.utils`, `requests.auth`)
- Key insight: Utilities do not reside on the Session class.

**Our implementation:**

- `Resume` class methods: Operations on Resume data only (`to_pdf()`, `to_html()`, `validate()`)
- `simple_resume.api.*` modules: Public stable API for utilities (`api.colors`)
- `core.*` modules: Internal implementation (not for public import)

### 2. Remove All Wrapper Functions

**Eliminated:**

- `utilities.calculate_text_color()` - wrapper removed
- `utilities.calculate_luminance()` - wrapper removed
- `color_utils.calculate_text_color()` - wrapper removed (module renamed to `core.colors`)
- `color_utils.validate_color()` - wrapper removed (module renamed to `core.colors`)
- `Resume.calculate_text_color()` - removed from class
- `Resume.validate_color()` - removed from class
- `Resume.calculate_luminance()` - removed from class

**Rationale:**

- No backward compatibility aliases, leading to a clean API surface.
- Each function exists in ONE authoritative location
- No wrappers that add zero value

### 3. Establish Public API Namespaces

**`simple_resume.api.colors`** - Public color utilities:

- `calculate_luminance()` - WCAG luminance calculation
- `is_valid_color()` - hex color validation
- `calculate_text_color()` - contrasting text color for background

**`simple_resume.core.Resume`** - Operations on Resume data:

- `Resume.read_yaml()` - Factory (like `pd.read_csv()`)
- `Resume.to_pdf()` - Export operation
- `Resume.to_html()` - Export operation
- `Resume.validate()` - Validate instance data
- `Resume.with_template()` - Method chaining
- `Resume.with_palette()` - Method chaining

### 4. Authoritative Function Names

Core module functions represent the canonical implementation:

- `core.colors.calculate_luminance()` - canonical
- `core.colors.get_contrasting_text_color()` - canonical
- `core.colors.is_valid_color()` - canonical

Public API re-exports or simplifies:

- `api.colors.calculate_luminance` - direct re-export
- `api.colors.is_valid_color` - direct re-export
- `api.colors.calculate_text_color()` - simplified interface that calls `core.colors.get_contrasting_text_color()`

## Rationale

### Why Remove Utilities from Resume Class?

Color utilities are pure functions that do not operate on Resume data. Following the requests pattern (e.g., `dict_from_cookiejar()` in `requests.utils`, not on Session class), we moved color utilities to their own module.

**Before (incorrect):**

```python
from simple_resume.core.resume import Resume
text_color = Resume.calculate_text_color("#FFFFFF")  # Why is this on Resume?


```text

**After (FCIS pattern):**
```python
from simple_resume.core import colors
text_color = colors.get_contrasting_text_color("#FFFFFF")  # Core utility


```text

### Why No Wrapper Functions?

Wrappers (e.g., `calculate_text_color = get_contrasting_text_color`) violate DRY, creating:
- Maintenance burden (two names for same function)
- Import confusion (which to use?)
- Documentation duplication
- Test duplication

Direct imports eliminate these issues.

### Why `core.*` Namespace? (Updated for FCIS)

With FCIS architecture (Functional Core, Imperative Shell):
- `core.*` contains pure functions with no I/O or side effects
- Color utilities are pure calculations - they belong in core
- No need for separate API layer when functions are already pure
- Direct imports from `core.*` are appropriate for library code

## Consequences

### Positive

- **Clearer API**: Utilities in dedicated modules, not scattered across classes
- **Industry alignment**: Matches pandas and requests patterns
- **No redundancy**: Each function in ONE authoritative location
- **Better discoverability**: `simple_resume.api.colors` is obvious for color utilities
- **Maintainable**: No wrapper functions to keep in sync
- **Testable**: All utilities tested in `test_api_colors.py`

### Negative

- **Breaking change**: Users importing from the `Resume` class must update their code.
- **Migration effort**: Tests must be moved to `test_api_colors.py`.

### Migration Path

**Before:**
```python
from simple_resume.core.resume import Resume

text_color = Resume.calculate_text_color("#FFFFFF")
is_valid = Resume.validate_color("#FF0000")
lum = Resume.calculate_luminance("#808080")


```text

**After (FCIS):**
```python
from simple_resume.core import colors

text_color = colors.get_contrasting_text_color("#FFFFFF")
is_valid = colors.is_valid_color("#FF0000")
lum = colors.calculate_luminance("#808080")


```text

Use `from simple_resume.core import colors` in all new code.

### Monitoring

- Track import patterns in user code (if telemetry added)
- Monitor GitHub issues for API confusion
- Code review checklist: ensure new utilities go in correct modules

## Follow-up Tasks

1. Remove color utility wrappers from `utilities.py`, `color_utils.py`, and the `Resume` class.
2. Create the `simple_resume.api.colors` public module.
3. Move color utility tests to `test_api_colors.py`.
4. Update `__all__` exports to include only authoritative functions.
5. Review other utility functions for similar issues (e.g., skill_utils)
6. Document public API in user guide
7. Add an API stability policy to CONTRIBUTING.md.

## References

- pandas API Documentation: <https://pandas.pydata.org/docs/reference/index.html>
- requests API Documentation: <https://requests.readthedocs.io/en/latest/api/>
- Functional Core, Imperative Shell: <https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell>
- ADR-002: Functional Core, Imperative Shell (related pattern)
