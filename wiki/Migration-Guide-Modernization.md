# Migration Guide: Functional Core, Imperative Shell Modernization

**Target Audience:** Users of simple-resume library
**Status:** In Progress
**Last Updated:** 2025-11-14
**Related:** [ARCHITECTURE.md](ARCHITECTURE.md), [ADR002](architecture/ADR002-functional-core-imperative-shell.md)

## Overview

simple-resume is undergoing architectural modernization to follow the "functional core, imperative shell" pattern. This guide helps you migrate your code to use the new APIs.

## Timeline

| Phase | Target Date | Changes | Impact |
|-------|-------------|---------|--------|
| Phase 1 (Foundation) | Week 1 | Architectural tests, documentation | None - Internal only |
| Phase 2 (PDF/HTML) | Week 2 | Internal refactoring | None - API unchanged |
| Phase 3 (Resume Class) | Week 3 | **Resume.read_yaml() deprecated** | **User-facing** |
| Phase 4 (Palette Config) | Week 4 | Internal refactoring | None - API unchanged |
| Phase 5 (Enforcement) | Week 5 | CI/CD gates | None - Development only |
| Phase 6 (Effect System) | Week 6 | Optional advanced pattern | Optional |
| Phase 7 (Documentation) | Week 7-8 | Complete docs | None |

## Breaking Changes Summary

### Phase 3: Resume Loading (Week 3)

**Status:** Planned for Week 3

**What's Changing:**
- `Resume.read_yaml()` classmethod → **Deprecated** (not removed)
- New preferred API: `resume_loaders.load_resume_from_yaml()`

**Why:**
Separates I/O operations (shell layer) from business logic (core layer), making the code more testable and maintainable.

**Migration:**

```python
# BEFORE (old API - still works with deprecation warning)
from simple_resume import Resume

resume = Resume.read_yaml("my_resume")
resume.to_pdf("output.pdf")

# AFTER (new API - recommended)
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml

resume = load_resume_from_yaml("my_resume")
resume.to_pdf("output.pdf")
```

**Backward Compatibility:**
- `Resume.read_yaml()` will continue to work with a deprecation warning
- Warning added in v1.x
- Method will be removed in v2.0 (future)

---

## Detailed Migration Examples

### 1. Resume Loading

#### Before
```python
from simple_resume import Resume

# Load resume
resume = Resume.read_yaml("my_resume", paths=["./resumes"])

# Generate PDF
resume.to_pdf("output.pdf")

# Generate HTML
resume.to_html("output.html")
```

#### After
```python
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml

# Load resume (now explicit I/O operation)
resume = load_resume_from_yaml("my_resume", paths=["./resumes"])

# Generate PDF (unchanged)
resume.to_pdf("output.pdf")

# Generate HTML (unchanged)
resume.to_html("output.html")
```

#### Why This Change?

**Before:** The `Resume` class (core domain model) was responsible for file I/O, making it:
- Hard to test without filesystem access
- Coupled to YAML format
- Mixed responsibilities (domain logic + I/O)

**After:** Responsibilities are separated:
- **Shell** (`resume_loaders`) - Handles file I/O, YAML parsing
- **Core** (`Resume`) - Pure domain logic, data transformations

**Benefits:**
- Test `Resume` without files
- Easy to support other formats (JSON, TOML)
- Clear separation of concerns

---

### 2. Custom Resume Processing

#### Before
```python
from simple_resume import Resume

class MyCustomResume(Resume):
    @classmethod
    def load_from_custom_source(cls, source_id: str):
        # Had to use Resume.read_yaml() internally
        return cls.read_yaml(source_id)
```

#### After
```python
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml

class MyCustomResume(Resume):
    @classmethod
    def load_from_custom_source(cls, source_id: str):
        # Use shell loader for I/O
        return load_resume_from_yaml(source_id)

    # Or load data first, then create Resume
    @classmethod
    def from_api_response(cls, api_data: dict):
        # Transform API data to resume format
        resume_data = transform_api_data(api_data)

        # Use pure factory method
        return cls.from_data(
            data=resume_data,
            name="api_resume",
        )
```

**New capability:** `Resume.from_data()` accepts pre-loaded data, making it easy to integrate with any data source (APIs, databases, etc.).

---

### 3. Testing Resume Processing

#### Before
```python
import pytest
from simple_resume import Resume
from pathlib import Path

def test_resume_generation():
    # Required actual YAML file on disk
    test_file = Path("test_fixtures/resume.yaml")
    test_file.write_text("""
    config:
      theme_color: "#0395DE"
    profile:
      name: "Test User"
    """)

    resume = Resume.read_yaml("resume", paths=["test_fixtures"])
    # ... test logic ...

    # Cleanup
    test_file.unlink()
```

#### After
```python
import pytest
from simple_resume import Resume

def test_resume_generation():
    # No files needed! Use pure factory
    resume_data = {
        "config": {"theme_color": "#0395DE"},
        "profile": {"name": "Test User"},
    }

    resume = Resume.from_data(resume_data, name="test")

    # Test business logic without I/O
    assert resume.config.theme_color == "#0395DE"
    # ... test logic ...

    # No cleanup needed!
```

**Benefits:**
- Faster tests (no file I/O)
- No test fixtures to manage
- Tests run in parallel safely
- Clear what data is being tested

---

## API Changes by Version

### Version 1.x (Current)

**Status:** Deprecation warnings added

**Changes:**
- ⚠️ `Resume.read_yaml()` - Deprecated, use `shell.resume_loaders.load_resume_from_yaml()`
- ✨ `Resume.from_data()` - New pure factory method
- ✨ `shell.resume_loaders.load_resume_from_yaml()` - New loader function

**Backward Compatibility:** All old APIs continue to work with warnings.

### Version 2.0 (Future)

**Status:** Planned (no date set)

**Breaking Changes:**
- ❌ `Resume.read_yaml()` - Removed
- ✅ Must use `shell.resume_loaders.load_resume_from_yaml()` or `Resume.from_data()`

---

## Upgrade Checklist

### For Library Users

- [ ] Review this migration guide
- [ ] Identify usage of `Resume.read_yaml()` in your code
- [ ] Replace with `shell.resume_loaders.load_resume_from_yaml()`
- [ ] Test with deprecation warnings enabled
- [ ] Update any custom Resume subclasses
- [ ] Update tests to use `Resume.from_data()` where appropriate

### For Contributors

- [ ] Read [ARCHITECTURE.md](ARCHITECTURE.md)
- [ ] Understand core/shell separation
- [ ] Run architectural tests: `pytest tests/architecture/`
- [ ] Follow import rules (no core → shell imports)
- [ ] Use dependency injection in new code
- [ ] Review [ADR002](architecture/ADR002-functional-core-imperative-shell.md)

---

## Code Search & Replace Patterns

### Search for Old Patterns

```bash
# Find usage of Resume.read_yaml()
grep -r "Resume\.read_yaml" --include="*.py" .

# Find imports that need updating
grep -r "from simple_resume import Resume" --include="*.py" .
```

### Automated Migration (if applicable)

```python
# migration_script.py
import re
from pathlib import Path

def migrate_file(file_path: Path):
    """Migrate a Python file to new API."""
    content = file_path.read_text()

    # Add new import if Resume.read_yaml is used
    if "Resume.read_yaml" in content:
        if "from simple_resume import Resume" in content:
            content = content.replace(
                "from simple_resume import Resume",
                "from simple_resume import Resume\n"
                "from simple_resume.shell.resume_loaders import load_resume_from_yaml"
            )

        # Replace calls
        content = re.sub(
            r'Resume\.read_yaml\(',
            r'load_resume_from_yaml(',
            content
        )

    file_path.write_text(content)

# Usage: migrate_file(Path("my_script.py"))
```

---

## Deprecation Warnings

When you run code using deprecated APIs, you'll see:

```
DeprecationWarning: Resume.read_yaml() is deprecated.
Use shell.resume_loaders.load_resume_from_yaml() instead.
```

### Handling Warnings

**Show all warnings:**
```bash
python -W all my_script.py
```

**Suppress warnings (temporary):**
```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

**Fix the code (recommended):**
```python
# Replace deprecated calls with new API
```

---

## Frequently Asked Questions

### Q: Why are you making these changes?

**A:** To improve code quality, testability, and maintainability. The functional core, imperative shell pattern:
- Makes business logic easier to test (no mocking required)
- Separates concerns clearly
- Enables faster test execution
- Reduces coupling to external dependencies

See [ADR002](architecture/ADR002-functional-core-imperative-shell.md) for detailed rationale.

### Q: Will my code break?

**A:** Not immediately. Deprecated methods will continue to work in v1.x with warnings. They'll be removed in v2.0 (future, no date set).

### Q: How much work is migration?

**A:** Minimal. Most changes are simple import updates:

```python
# Change this:
resume = Resume.read_yaml("name")

# To this:
resume = load_resume_from_yaml("name")
```

For most users, this is a 5-10 minute update.

### Q: What if I have custom Resume subclasses?

**A:** Update them to use the new loaders or `from_data()` factory:

```python
class MyResume(Resume):
    @classmethod
    def load_custom(cls, source):
        data = fetch_from_custom_source(source)
        return cls.from_data(data, name=source)
```

### Q: Can I continue using old APIs?

**A:** Yes, for now. But we recommend migrating proactively to:
- Avoid sudden breakage in v2.0
- Benefit from better testability
- Follow best practices

### Q: When will v2.0 be released?

**A:** Not yet scheduled. We'll provide at least 6 months notice before removing deprecated APIs.

### Q: Where can I get help?

**A:**
- Review this guide
- Check [ARCHITECTURE.md](ARCHITECTURE.md)
- Read [ADR002](architecture/ADR002-functional-core-imperative-shell.md)
- Open a GitHub issue with migration questions

---

## Examples Gallery

### Example 1: Simple Script

**Before:**
```python
#!/usr/bin/env python3
from simple_resume import Resume

resume = Resume.read_yaml("john_doe")
resume.to_pdf("john_doe.pdf")
print("PDF generated!")
```

**After:**
```python
#!/usr/bin/env python3
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml

resume = load_resume_from_yaml("john_doe")
resume.to_pdf("john_doe.pdf")
print("PDF generated!")
```

### Example 2: Batch Processing

**Before:**
```python
from simple_resume import Resume
from pathlib import Path

resume_dir = Path("./resumes")
output_dir = Path("./output")

for yaml_file in resume_dir.glob("*.yaml"):
    name = yaml_file.stem
    resume = Resume.read_yaml(name, paths=["./resumes"])
    resume.to_pdf(output_dir / f"{name}.pdf")
```

**After:**
```python
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml
from pathlib import Path

resume_dir = Path("./resumes")
output_dir = Path("./output")

for yaml_file in resume_dir.glob("*.yaml"):
    name = yaml_file.stem
    resume = load_resume_from_yaml(name, paths=["./resumes"])
    resume.to_pdf(output_dir / f"{name}.pdf")
```

### Example 3: Web Application

**Before:**
```python
from flask import Flask, request, send_file
from simple_resume import Resume
from pathlib import Path

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate_resume():
    resume_name = request.form["resume_name"]

    resume = Resume.read_yaml(resume_name, paths=["./data/resumes"])

    output_path = Path(f"/tmp/{resume_name}.pdf")
    resume.to_pdf(str(output_path))

    return send_file(output_path, as_attachment=True)
```

**After:**
```python
from flask import Flask, request, send_file
from simple_resume import Resume
from simple_resume.shell.resume_loaders import load_resume_from_yaml
from pathlib import Path

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate_resume():
    resume_name = request.form["resume_name"]

    # Use shell loader for I/O
    resume = load_resume_from_yaml(resume_name, paths=["./data/resumes"])

    output_path = Path(f"/tmp/{resume_name}.pdf")
    resume.to_pdf(str(output_path))

    return send_file(output_path, as_attachment=True)
```

### Example 4: Testing (Best Example)

**Before:**
```python
import unittest
from simple_resume import Resume
from pathlib import Path
import tempfile

class TestResumeGeneration(unittest.TestCase):
    def setUp(self):
        # Create temporary directory and file
        self.temp_dir = tempfile.mkdtemp()
        self.resume_file = Path(self.temp_dir) / "test.yaml"
        self.resume_file.write_text("""
config:
  theme_color: "#0395DE"
  page_width: 210
  page_height: 297
profile:
  name: "Test User"
  email: "test@example.com"
        """)

    def tearDown(self):
        # Clean up temporary files
        self.resume_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_resume_loads(self):
        resume = Resume.read_yaml("test", paths=[self.temp_dir])
        self.assertEqual(resume.name, "test")
```

**After:**
```python
import unittest
from simple_resume import Resume

class TestResumeGeneration(unittest.TestCase):
    # No setUp or tearDown needed!

    def test_resume_loads(self):
        # Pure data - no files!
        resume_data = {
            "config": {
                "theme_color": "#0395DE",
                "page_width": 210,
                "page_height": 297,
            },
            "profile": {
                "name": "Test User",
                "email": "test@example.com",
            },
        }

        # Use pure factory
        resume = Resume.from_data(resume_data, name="test")

        # Test business logic
        self.assertEqual(resume.name, "test")
        self.assertEqual(resume.config.theme_color, "#0395DE")
```

**Benefits of new testing approach:**
- 10x faster (no file I/O)
- No cleanup needed
- No temp directories
- Clear test data
- Can run in parallel

---

## Future Changes (Phase 2+)

### Phase 2: PDF/HTML Generation (Internal Only)

**Status:** Planned for Week 2

**Changes:** Internal refactoring of PDF/HTML generation
**User Impact:** None - APIs unchanged
**Benefits:** Faster tests, better code organization

### Phase 4: Palette Configuration (Internal Only)

**Status:** Planned for Week 4

**Changes:** Internal refactoring of palette color fetching
**User Impact:** None - APIs unchanged
**Benefits:** Better error handling, testability

---

## Getting Help

**Documentation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture guide
- [ADR002](architecture/ADR002-functional-core-imperative-shell.md) - Decision rationale
- [CORE_REFACTOR_PLAN.md](../CORE_REFACTOR_PLAN.md) - Implementation plan

**Support:**
- GitHub Issues: Report migration problems
- Code reviews: Ask for feedback on migrations
- Architecture sessions: Join discussions

---

**Document maintained by:** Architecture team
**Last updated:** 2025-11-14
**Version:** 1.0
