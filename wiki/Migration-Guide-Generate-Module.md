# Migration Guide: Generate Module Reorganization

## Overview

This guide covers migrating to the new `simple_resume.shell.generate` module structure (v0.1.1). The reorganization improves performance with lazy loading and enhances code organization.

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
import simple_resume.shell.generate

# Function access remains the same
result = simple_resume.shell.generate.generate_pdf(resume_data)
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
from simple_resume.shell.generate import core, lazy

print("Migration successful!")
```

### 3. Performance Considerations

The new structure provides both lazy and eager loading options:

#### Lazy Loading (Default)
- **Suited for**: CLI tools, scripts, applications where generation is optional
- **Benefits**: Faster startup, lower memory footprint
- **Usage**: Default main API imports

```python
from simple_resume import generate_pdf  # Lazy loaded
```

#### Eager Loading
- **Suited for**: Web applications, services where generation is always used
- **Benefits**: Predictable performance when generation is called
- **Usage**: Direct core module imports

```python
from simple_resume.shell.generate.core import generate_pdf  # Eager loaded
```

## Compatibility Matrix

| Previous Import | New Import | Compatibility |
|----------------|------------|---------------|
| `simple_resume.generation` | `simple_resume` | Drop-in replacement |
| `simple_resume.generation.GenerationConfig` | `simple_resume.core.models.GenerationConfig` | Path changed |
| `simple_resume.generation.*functions` | `simple_resume.shell.generate.*functions` | Path changed |

## Common Migration Patterns

### CLI Applications
```python
# Before
from simple_resume.generation import generate_pdf, GenerationConfig

# After (recommended - lazy loading)
from simple_resume import generate_pdf
from simple_resume.core.models import GenerationConfig

# Or direct import for slightly better performance
from simple_resume.shell.generate.lazy import generate_pdf
```

### Web Applications
```python
# Before
from simple_resume.generation import generate_all, GenerationConfig

# After (recommended - eager loading)
from simple_resume.shell.generate.core import generate_all
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
from simple_resume.shell.generate.core import generate_pdf
```

## Testing Your Migration

### Basic Functionality Test
```python
from simple_resume import generate_pdf, generate_html, generate_all
from simple_resume.shell.generate import core, lazy
from simple_resume.core.models import GenerationConfig

def test_migration():
    """Test that imports work correctly after migration."""
    try:
        # Test main API
        print("OK Main API imports work")

        # Test module structure
        print("OK Module structure works")

        # Test GenerationConfig
        config = GenerationConfig()
        print("OK GenerationConfig works")

        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
```

### Performance Test
```python
import time
import sys
import importlib

def test_import_performance():
    """Compare import performance between approaches."""

    # Clear any existing imports
    modules_to_remove = [k for k in sys.modules.keys() if "simple_resume" in k]
    for module in modules_to_remove:
        del sys.modules[module]

    # Test lazy loading
    start = time.time()
    simple_resume = importlib.import_module("simple_resume")
    generate_pdf = simple_resume.shell.generate_pdf
    lazy_time = time.time() - start

    # Clear imports between tests
    modules_to_remove = [k for k in sys.modules.keys() if "simple_resume" in k]
    for module in modules_to_remove:
        del sys.modules[module]

    # Test eager loading
    start = time.time()
    simple_resume_generate_core = importlib.import_module("simple_resume.shell.generate.core")
    eager_pdf = simple_resume_generate_core.generate_pdf
    eager_time = time.time() - start

    print(f"Lazy loading: {lazy_time:.4f}s")
    print(f"Eager loading: {eager_time:.4f}s")
```

## When to Use Each Approach

### Use Lazy Loading When:
- Building CLI tools or scripts
- Generation functionality is optional
- Memory efficiency is important
- Startup time matters

### Use Eager Loading When:
- Building web applications or services
- Generation functionality is always used
- Predictable response times are critical
- Initial import time is less important than runtime performance

## Get Help

- Check the [Usage Guide](Usage-Guide.md) for detailed usage examples
- Review the [Architecture Decisions](../architecture/) for technical details
- Open an issue for questions or problems
