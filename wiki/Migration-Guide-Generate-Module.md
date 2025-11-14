# Migration Guide: Generate Module Reorganization

## Overview

This guide helps users migrate their code to use the new `simple_resume.generate` module structure introduced in v0.2.0. The reorganization improves performance through lazy loading and provides better code organization.

## Breaking Changes

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
from simple_resume.generate import generate_pdf, generate_html, generate_all

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

## Migration Steps

### 1. Update Import Statements

#### Simple Usage (Recommended)
```python
# Before
from simple_resume.generation import generate_pdf, generate_html

# After (no changes needed if using main API)
from simple_resume import generate_pdf, generate_html
```

#### Advanced Usage
```python
# Before
import simple_resume.generation

# After
import simple_resume.generate

# Function access remains the same
result = simple_resume.generate.generate_pdf(resume_data)
```

#### GenerationConfig Access
```python
# Before
from simple_resume.generation import GenerationConfig

# After
from simple_resume.core.models import GenerationConfig
```

### 2. Test Import Changes

Verify your imports work correctly:

```python
# Test basic functionality
from simple_resume import generate_pdf, generate_html, generate_all
from simple_resume.core.models import GenerationConfig

# Test module access
from simple_resume.generate import core, lazy

print("Migration successful!")
```

### 3. Performance Considerations

The new structure provides both lazy and eager loading options:

#### Lazy Loading (Default)
- **Best for**: CLI tools, scripts, applications where generation might not be used
- **Benefits**: Faster startup, lower memory footprint
- **Usage**: Default main API imports

```python
from simple_resume import generate_pdf  # Lazy loaded
```

#### Eager Loading
- **Best for**: Web applications, services where generation is always used
- **Benefits**: Predictable performance when generation is called
- **Usage**: Direct core module imports

```python
from simple_resume.generate.core import generate_pdf  # Eager loaded
```

## Compatibility Matrix

| Previous Import | New Import | Compatibility |
|----------------|------------|---------------|
| `simple_resume.generation` | `simple_resume` | ✅ Drop-in replacement |
| `simple_resume.generation.GenerationConfig` | `simple_resume.core.models.GenerationConfig` | ⚠️ Path changed |
| `simple_resume.generation.*functions` | `simple_resume.generate.*functions` | ⚠️ Path changed |

## Common Migration Patterns

### CLI Applications
```python
# Before
from simple_resume.generation import generate_pdf, GenerationConfig

# After (recommended - lazy loading)
from simple_resume import generate_pdf
from simple_resume.core.models import GenerationConfig

# Or direct import for slightly better performance
from simple_resume.generate.lazy import generate_pdf
```

### Web Applications
```python
# Before
from simple_resume.generation import generate_all, GenerationConfig

# After (recommended - eager loading)
from simple_resume.generate.core import generate_all
from simple_resume.core.models import GenerationConfig
```

### Library Code
```python
# Before
from simple_resume.generation import generate_resume

# After (recommended - flexible)
from simple_resume import generate_resume  # Default lazy loading
```

## Troubleshooting

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'simple_resume.generation'`

**Solution**: Update import paths:
```python
# Replace
from simple_resume.generation import generate_pdf

# With
from simple_resume import generate_pdf
```

**Error**: `ImportError: cannot import name 'GenerationConfig' from 'simple_resume.generation'`

**Solution**: Update GenerationConfig import:
```python
# Replace
from simple_resume.generation import GenerationConfig

# With
from simple_resume.core.models import GenerationConfig
```

### Performance Issues

If you experience slower first-time generation calls, this is expected due to lazy loading. For consistent performance in high-throughput scenarios, use eager loading:

```python
# Instead of lazy loading
from simple_resume import generate_pdf

# Use eager loading
from simple_resume.generate.core import generate_pdf
```

## Testing Your Migration

### Basic Functionality Test
```python
def test_migration():
    """Test that imports work correctly after migration."""
    try:
        # Test main API
        from simple_resume import generate_pdf, generate_html, generate_all
        print("✓ Main API imports work")

        # Test module structure
        from simple_resume.generate import core, lazy
        print("✓ Module structure works")

        # Test GenerationConfig
        from simple_resume.core.models import GenerationConfig
        config = GenerationConfig()
        print("✓ GenerationConfig works")

        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
```

### Performance Test
```python
import time

def test_import_performance():
    """Compare import performance between approaches."""

    # Test lazy loading
    start = time.time()
    from simple_resume import generate_pdf
    lazy_time = time.time() - start

    # Test eager loading
    start = time.time()
    from simple_resume.generate.core import generate_pdf
    eager_time = time.time() - start

    print(f"Lazy loading: {lazy_time:.4f}s")
    print(f"Eager loading: {eager_time:.4f}s")
```

## When to Use Each Approach

### Use Lazy Loading When:
- Building CLI tools or scripts
- Generation functionality might not be used
- Memory efficiency is important
- Startup time matters

### Use Eager Loading When:
- Building web applications or services
- Generation functionality is always used
- Predictable response times are critical
- Initial import time is less important than runtime performance

## Need Help?

- Check the [Usage Guide](Usage-Guide.md) for detailed usage examples
- Review the [Architecture Decisions](../architecture/) for technical details
- Open an issue for questions or problems

## Timeline

- **v0.2.0**: New module structure introduced
- **v0.3.0**: Old imports will show deprecation warnings
- **v0.4.0**: Old imports will be removed

Migration is recommended but not immediately required. Old imports will continue to work in v0.2.x with warnings.
