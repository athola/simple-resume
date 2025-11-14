# Lazy Loading Guide

## Overview

Simple Resume v0.2.0 introduces lazy loading for the generation module, providing better startup performance and reduced memory footprint for applications that may not always use resume generation functionality.

## What is Lazy Loading?

Lazy loading defers importing heavy modules until they're actually needed, rather than loading everything at import time. This provides several benefits:

- **Faster Startup**: Applications start quicker since fewer modules are loaded initially
- **Lower Memory Usage**: Only used functionality consumes memory
- **Better Performance**: For applications that don't use generation, there's zero overhead

## Usage Patterns

### 1. Default Lazy Loading (Recommended)

The main API uses lazy loading by default:

```python
from simple_resume import generate_pdf, generate_html, generate_all

# Functions are lazy-loaded when first called
result = generate_pdf("resume.yaml", output_dir="output/")
```

**Best for:**
- CLI tools and scripts
- Applications where generation might not be used
- Memory-constrained environments

### 2. Explicit Lazy Loading

For more control over lazy loading:

```python
from simple_resume.generate.lazy import generate_pdf, generate_html

# Generation modules only loaded when functions are called
result = generate_html("resume.yaml", preview_mode=True)
```

**Best for:**
- When you want explicit control over loading
- Mixed-use applications
- Performance-critical startup scenarios

### 3. Eager Loading

For predictable performance when generation is always used:

```python
from simple_resume.generate.core import generate_pdf, generate_html

# All generation modules loaded immediately
result = generate_pdf("resume.yaml", output_dir="output/")
```

**Best for:**
- Web applications and services
- High-throughput generation scenarios
- When predictable response times are critical

## Performance Comparison

### Import Time

```python
import time

# Test lazy loading
start = time.time()
from simple_resume import generate_pdf
lazy_import_time = time.time() - start

# Test eager loading
start = time.time()
from simple_resume.generate.core import generate_pdf
eager_import_time = time.time() - start

print(f"Lazy import: {lazy_import_time:.4f}s")
print(f"Eager import: {eager_import_time:.4f}s")
```

### Memory Usage

```python
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

# Test memory with lazy loading
initial_memory = get_memory_usage()
from simple_resume import generate_pdf
lazy_memory = get_memory_usage()

# Test memory with eager loading
from simple_resume.generate.core import generate_pdf
eager_memory = get_memory_usage()

print(f"Initial memory: {initial_memory:.1f} MB")
print(f"After lazy import: {lazy_memory:.1f} MB")
print(f"After eager import: {eager_memory:.1f} MB")
```

## Common Scenarios

### CLI Applications

**✅ Recommended: Use lazy loading**

```python
#!/usr/bin/env python3
"""CLI tool that generates resumes."""

import argparse
from simple_resume import generate_pdf, generate_html, preview

def main():
    parser = argparse.ArgumentParser(description="Generate resumes")
    parser.add_argument("resume", help="Resume YAML file")
    parser.add_argument("--format", choices=["pdf", "html", "all"], default="pdf")
    parser.add_argument("--preview", action="store_true")

    args = parser.parse_args()

    if args.preview:
        preview(args.resume)
    elif args.format == "pdf":
        generate_pdf(args.resume, output_dir="output/")
    elif args.format == "html":
        generate_html(args.resume, output_dir="output/")
    else:
        from simple_resume import generate_all
        generate_all(args.resume, formats=["pdf", "html"], output_dir="output/")

if __name__ == "__main__":
    main()
```

**Benefits:**
- Fast startup even if generation isn't needed
- Low memory overhead
- Functions only loaded when actually used

### Web Applications

**✅ Recommended: Use eager loading**

```python
"""FastAPI web service for resume generation."""

from fastapi import FastAPI, UploadFile
from simple_resume.generate.core import generate_pdf, generate_html
from simple_resume.core.models import GenerationConfig

app = FastAPI()

@app.post("/generate/pdf")
async def generate_pdf_endpoint(file: UploadFile):
    """Generate PDF resume with predictable performance."""
    # Generation modules already loaded, no delay
    content = await file.read()
    result = generate_pdf(content, output_dir="/tmp/output/")
    return {"success": True, "output_path": result.output_path}

@app.post("/generate/html")
async def generate_html_endpoint(file: UploadFile):
    """Generate HTML resume with predictable performance."""
    content = await file.read()
    result = generate_html(content, preview_mode=True)
    return {"success": True, "output_path": result.output_path}
```

**Benefits:**
- Predictable response times
- No first-request delay
- Consistent performance

### Library Code

**✅ Recommended: Use lazy loading**

```python
"""Library that optionally provides resume generation."""

class DocumentProcessor:
    """Processes documents with optional resume generation."""

    def __init__(self):
        # Don't load generation modules until needed
        self._generation_loaded = False

    def _load_generation(self):
        """Lazy load generation functionality."""
        if not self._generation_loaded:
            from simple_resume import generate_pdf, generate_html
            self.generate_pdf = generate_pdf
            self.generate_html = generate_html
            self._generation_loaded = True

    def process_document(self, doc_path: str, generate_resume: bool = False):
        """Process a document, optionally generating resume."""
        # Regular document processing
        self._process_content(doc_path)

        # Only load generation if needed
        if generate_resume:
            self._load_generation()
            self.generate_pdf(doc_path, output_dir="output/")

    def _process_content(self, doc_path: str):
        """Regular document processing logic."""
        pass
```

**Benefits:**
- Zero overhead for users who don't need generation
- Conditional functionality loading
- Flexible API design

## Advanced Usage

### Conditional Lazy Loading

```python
class ResumeGenerator:
    """Lazy-loaded resume generator with conditions."""

    def __init__(self, lazy: bool = True):
        self.lazy = lazy
        self._core = None

    @property
    def core(self):
        """Lazy load core module."""
        if self._core is None and not self.lazy:
            from simple_resume.generate import core
            self._core = core
        return self._core

    def generate_pdf(self, *args, **kwargs):
        """Generate PDF with optional lazy loading."""
        if self.lazy:
            from simple_resume.generate.lazy import generate_pdf
            return generate_pdf(*args, **kwargs)
        else:
            return self.core.generate_pdf(*args, **kwargs)
```

### Performance Profiling

```python
import time
import tracemalloc

def profile_generation_performance():
    """Profile different loading approaches."""

    # Test lazy loading performance
    tracemalloc.start()

    lazy_start = time.time()
    from simple_resume import generate_pdf
    lazy_import_time = time.time() - lazy_start

    # First call (triggers lazy load)
    call_start = time.time()
    # Note: This would need actual resume data to work
    # result = generate_pdf("test.yaml")
    lazy_call_time = time.time() - call_start

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Lazy Import Time: {lazy_import_time:.4f}s")
    print(f"Lazy First Call: {lazy_call_time:.4f}s")
    print(f"Memory Usage: {current_memory / 1024 / 1024:.1f} MB")
    print(f"Peak Memory: {peak_memory / 1024 / 1024:.1f} MB")
```

## Best Practices

### 1. Choose the Right Approach

```python
# Use lazy loading for:
# - CLI tools
# - Scripts
# - Optional functionality
from simple_resume import generate_pdf

# Use eager loading for:
# - Web services
# - High-throughput applications
# - Always-used functionality
from simple_resume.generate.core import generate_pdf
```

### 2. Handle Lazy Loading Errors

```python
try:
    from simple_resume import generate_pdf
    result = generate_pdf("resume.yaml")
except ImportError as e:
    print(f"Generation functionality not available: {e}")
    # Fallback behavior
```

### 3. Profile Your Application

```python
import time

def profile_imports():
    """Profile import performance for your use case."""

    approaches = [
        ("Lazy", "from simple_resume import generate_pdf"),
        ("Eager", "from simple_resume.generate.core import generate_pdf"),
        ("Explicit Lazy", "from simple_resume.generate.lazy import generate_pdf"),
    ]

    for name, import_stmt in approaches:
        start = time.time()
        exec(import_stmt)
        end = time.time()
        print(f"{name}: {end - start:.4f}s")
```

### 4. Test Both Approaches

```python
def test_generation_works():
    """Test that both lazy and eager loading work."""

    # Test lazy loading
    from simple_resume import generate_pdf
    assert callable(generate_pdf)

    # Test eager loading
    from simple_resume.generate.core import generate_pdf as eager_pdf
    assert callable(eager_pdf)

    # Test explicit lazy loading
    from simple_resume.generate.lazy import generate_pdf as lazy_pdf
    assert callable(lazy_pdf)

    print("All loading approaches work correctly!")
```

## Migration Tips

### From Legacy Code

```python
# Old approach
import simple_resume.generation

# New approach (lazy)
from simple_resume import generate_pdf, generate_html

# Or new approach (eager)
from simple_resume.generate.core import generate_pdf, generate_html
```

### Performance Monitoring

```python
import time
import logging

# Set up performance logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timed_generate_pdf(*args, **kwargs):
    """Generate PDF with timing."""
    start = time.time()
    from simple_resume import generate_pdf

    result = generate_pdf(*args, **kwargs)
    end = time.time()

    logger.info(f"PDF generation took {end - start:.2f}s")
    return result
```

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure you're using the correct import paths
2. **Performance Issues**: Try eager loading for consistent performance
3. **Memory Issues**: Use lazy loading to reduce memory footprint

### Debugging Lazy Loading

```python
import sys

def debug_imports():
    """Debug what modules are loaded."""
    print("Loaded modules:")
    for module_name in sorted(sys.modules.keys()):
        if "simple_resume" in module_name:
            print(f"  {module_name}")
```

### Performance Comparison Script

```python
#!/usr/bin/env python3
"""Compare lazy vs eager loading performance."""

import time
import tracemalloc

def benchmark_approaches():
    """Benchmark different loading approaches."""

    print("📊 Simple Resume Loading Performance Benchmark")
    print("=" * 50)

    approaches = [
        ("Lazy Loading", "from simple_resume import generate_pdf"),
        ("Eager Loading", "from simple_resume.generate.core import generate_pdf"),
        ("Explicit Lazy", "from simple_resume.generate.lazy import generate_pdf"),
    ]

    results = {}

    for name, import_stmt in approaches:
        # Clear any existing imports
        modules_to_remove = [k for k in sys.modules.keys() if "simple_resume" in k]
        for module in modules_to_remove:
            del sys.modules[module]

        # Benchmark import time
        tracemalloc.start()
        start = time.time()
        exec(import_stmt)
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results[name] = {
            "import_time": import_time,
            "memory_kb": current / 1024,
            "peak_memory_kb": peak / 1024
        }

        print(f"{name}:")
        print(f"  Import Time: {import_time:.4f}s")
        print(f"  Memory: {current / 1024:.1f} KB")
        print(f"  Peak Memory: {peak / 1024:.1f} KB")
        print()

    return results

if __name__ == "__main__":
    benchmark_approaches()
```

## Conclusion

Lazy loading in Simple Resume provides flexibility for different use cases:

- **Use lazy loading** for CLI tools and optional functionality
- **Use eager loading** for web services and always-used features
- **Profile your application** to choose the best approach

The default API uses lazy loading to provide good performance for most use cases while maintaining backward compatibility.
