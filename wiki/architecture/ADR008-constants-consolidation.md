# ADR 008: Constants Consolidation and Reorganization

## Status

**Accepted** (2025-11-13)

## Context

The simple-resume project accumulated constants scattered across multiple files with inconsistent organization:

- `src/simple_resume/constants.py` - Mixed constants (layout, files, defaults, validation)
- `src/simple_resume/core/color_utils.py` - Color-specific constants
- Duplicate or similar constants with different names
- Constants spread across different modules without clear organization

This led to:
- Difficulty discovering and using constants
- Inconsistent naming conventions
- Code duplication and increased maintenance overhead
- Unclear relationships between related constants

## Decision

We consolidated and reorganized all constants into a dedicated `constants/` module, ensuring clear separation of concerns:

### New Structure
```
src/simple_resume/constants/
├── __init__.py         # Main exports and legacy compatibility
├── colors.py           # Color-related constants and palettes
├── files.py            # File extensions and path constants
├── layout.py           # Layout and dimension constants
└── validation.py       # Validation limits and thresholds
```

### Key Changes

#### 1. Layout Constants
**Before:**
```python
# Scattered across files
DEFAULT_PAGE_WIDTH_MM = 210
DEFAULT_PAGE_HEIGHT_MM = 297
SIDEBAR_WIDTH_MM = 50
# ... in constants.py

# Unused constants
A4_PAGE_WIDTH_MM = 210.0
A4_PAGE_HEIGHT_MM = 297.0
```

**After:**
```python
# Consolidated in constants/layout.py
DEFAULT_PAGE_WIDTH_MM: Final[int] = 190
DEFAULT_PAGE_HEIGHT_MM: Final[int] = 270
DEFAULT_SIDEBAR_WIDTH_MM: Final[int] = 50

# Establishes resume-specific dimensions (excluding full A4 standard)
```

#### 2. Color Constants
**Before:**
```python
# In core/color_utils.py
DEFAULT_THEME_COLOR = "#0395DE"
DEFAULT_SIDEBAR_COLOR = "#F6F6F6"
# Mixed with utility functions
```

**After:**
```python
# In constants/colors.py
DEFAULT_THEME_COLOR: Final[str] = "#0395DE"
DEFAULT_SIDEBAR_COLOR: Final[str] = "#F6F6F6"
# Grouped with other color constants
```

#### 3. File Constants
**Before:**
```python
# Mixed in main constants.py
PDF_EXTENSION = ".pdf"
HTML_EXTENSION = ".html"
TEX_EXTENSION = ".tex"
```

**After:**
```python
# In constants/files.py
PDF_EXTENSION: Final[str] = ".pdf"
HTML_EXTENSION: Final[str] = ".html"
TEX_EXTENSION: Final[str] = ".tex"
```

#### 4. Removal of Unused Constants
Removed `A4_PAGE_WIDTH_MM` and `A4_PAGE_HEIGHT_MM` because:
- The codebase never used them.
- `DEFAULT_PAGE_*_MM` provides the actual resume dimensions (with margins)
- A4 standard dimensions are well-known and don't need to be duplicated

## Rationale

### Benefits

1. **Improved Discoverability**: Constants are organized by domain (e.g., colors, layout, files).

2. **Better Maintainability**: Grouped related constants simplify updates.

3. **Reduced Code Size**: Elimination of ~900 lines of unused or deprecated code.

4. **Clearer Semantics**: Constants now possess clear purposes and relationships.

5. **Type Safety**: Proper type annotations with `Final` are added where appropriate.

6. **Legacy Compatibility**: The main `__init__.py` maintains backward compatibility.

### Design Principles

1. **Domain Organization**: Group constants by logical domain (e.g., colors, layout, files).

2. **Semantic Clarity**: Constant names clearly convey their purpose.

3. **Type Safety**: Use `Final` for true constants that remain unchanged.

4. **Backward Compatibility**: Maintain existing imports via re-exports.

5. **Minimal Surface Area**: Expose only constants that are actively used.

## Consequences

### Positive

- **Reduced Memory Footprint**: Eliminating unused constants saves ~44KB of memory.
- **Faster Imports**: Fewer modules to load and process.
- **Better IDE Support**: Enhanced autocomplete and navigation.
- **Clearer Dependencies**: Simplifies understanding of constant requirements per module.
- **Easier Testing**: Constants are easily mocked or overridden in tests.

### Negative

- **Import Changes**: Some code may require import path updates.
- **Learning Curve**: Developers must learn the new organization.
- **Migration Effort**: Existing code may require minimal updates.

### Neutral

- **Runtime Performance**: No significant change in execution performance
- **API Compatibility**: The main API remains unchanged via re-exports.

## Migration Guide

### For Library Users
No changes are needed; main API imports remain the same:

```python
# This still works
from simple_resume.constants import DEFAULT_PAGE_WIDTH_MM
```

### For Internal Development
For clarity, use specific constant modules:

```python
# Recommended for new code
from simple_resume.constants.layout import DEFAULT_PAGE_WIDTH_MM
from simple_resume.constants.colors import DEFAULT_THEME_COLOR
```

### For Constant Discovery
To discover constants, browse the organized modules:

```python
# See all layout constants
from simple_resume.constants import layout
print(dir(layout))

# See all color constants
from simple_resume.constants import colors
print(dir(colors))
```

## Implementation Details

### Exports Strategy
The main `constants/__init__.py` re-exports commonly used constants to ensure backward compatibility:

```python
# Re-export common constants
from .layout import DEFAULT_PAGE_WIDTH_MM, DEFAULT_PAGE_HEIGHT_MM
from .colors import DEFAULT_THEME_COLOR, DEFAULT_SIDEBAR_COLOR
from .files import PDF_EXTENSION, HTML_EXTENSION
```

### Naming Conventions
- Use `UPPER_SNAKE_CASE` for all constants.
- Include domain prefixes when clarity is needed.
- Use `Final` type annotation for true constants.
- Group related constants.

### Documentation
Each module features clear docstrings explaining:
- Purpose of the constants
- Relationships between constants
- Usage patterns where relevant

## Future Considerations

### Possible Extensions
1. **Dynamic Constants**: Explore adding support for environment-based constants.
2. **Validation**: Implement runtime validation for constant values.
3. **Generation**: Explore auto-generating constants from config files.

### Monitoring
1. **Usage Analysis**: Monitor the actual usage of constants.
2. **Performance**: Track import times using the new structure.
3. **Feedback**: Gather developer feedback on the organization.

### Deprecation Timeline
- **v0.1.1**: New structure introduced (current)
- **v0.2.0**: Introduce deprecation warnings for direct module imports.
- **v0.3.0**: Remove legacy re-exports; require specific module imports.

## Alternatives Considered

### Alternative 1: Keep Single File
- *Pros*: No import changes needed
- *Cons*: Continued maintenance overhead and poor organization.

### Alternative 2: Use Data Classes
- *Pros*: Offers type safety and grouped related constants.
- *Cons*: More complex and overkill for simple values.

### Alternative 3: Configuration Files
- *Pros*: Enables external configuration and easy modification.
- *Cons*: Introduces runtime overhead and a more complex build process.

The chosen approach provides the best balance of organization, performance, and maintainability.

## References

- [ADR 002: Functional Core, Imperative Shell](ADR002-functional-core-imperative-shell.md)
- [ADR 003: API Surface Design](ADR003-api-surface-design.md)
- [Code Organization Best Practices](https://docs.python.org/3/tutorial/modules.html)
- [Type Annotations Best Practices](https://peps.python.org/pep-0585/)
