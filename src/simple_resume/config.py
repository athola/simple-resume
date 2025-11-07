#!/usr/bin/env python3
"""Configuration helpers and shared constants.

## Path Handling Guidelines

simple-resume follows the **Path-first principle** for consistent path handling:

1. **Accept `str | Path` at API boundaries** for flexibility
2. **Normalize to `Path` immediately** after receiving input
3. **Use `Path` objects internally** throughout the codebase
4. **Convert to `str` only when required** by external APIs

### When to Convert to String

Only convert Path → str when:
- External libraries require strings (e.g., WeasyPrint's `write_pdf(str)`)
- Storing in exception messages (handled automatically in exception __init__)
- Building error messages for display

### Examples

```python
# ✓ Good: Accept both, normalize early
def process_file(file_path: str | Path) -> None:
    path = Path(file_path)  # Normalize immediately
    path.read_text()  # Use Path methods


# ✓ Good: Pass Path objects directly
output_path = paths.output / "resume.pdf"
resume.to_pdf(output_path)  # No conversion needed

# ✓ Good: Convert only when external API requires it
html_doc.write_pdf(str(output_path))  # WeasyPrint needs str

# ✗ Bad: Unnecessary conversions
output_path = str(paths.output) + "/resume.pdf"  # Use Path /
raise Error(f"Failed: {str(output_path)}")  # Path works in f-strings
```

### Paths Dataclass

The `Paths` dataclass stores all paths as `Path` objects:
- Immutable (frozen=True)
- Type-safe
- Supports pathlib operations

```python
paths = resolve_paths(data_dir="resume_private")
output_file = paths.output / "resume.pdf"  # Path operations
"""

from __future__ import annotations

import atexit
import os
from contextlib import ExitStack
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

# Keep an open handle to package resources so they're available even when the
# distribution is zipped (e.g., installed from a wheel).
_asset_stack = ExitStack()
PACKAGE_ROOT = _asset_stack.enter_context(
    resources.as_file(resources.files("simple_resume"))
)
atexit.register(_asset_stack.close)

PATH_CONTENT = PACKAGE_ROOT
TEMPLATE_LOC = PACKAGE_ROOT / "templates"
STATIC_LOC = PACKAGE_ROOT / "static"

# Legacy string-based paths preserved for backwards compatibility.
PATH_DATA = "resume_private"
PATH_INPUT = f"{PATH_DATA}/input"
PATH_OUTPUT = f"{PATH_DATA}/output"


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations used when rendering resumes."""

    data: Path
    input: Path
    output: Path
    content: Path = PATH_CONTENT
    templates: Path = TEMPLATE_LOC
    static: Path = STATIC_LOC


PathLike = str | os.PathLike[str]


def resolve_paths(
    data_dir: PathLike | None = None,
    *,
    content_dir: PathLike | None = None,
    templates_dir: PathLike | None = None,
    static_dir: PathLike | None = None,
) -> Paths:
    """Return the active data, input, and output paths.

    Args:
        data_dir: Optional directory containing `input/` and `output/` folders.
            When omitted, the RESUME_DATA_DIR environment variable is used. If
            neither is provided, the default is ./resume_private relative to the
            process working directory.
        content_dir: Optional override for the package content directory.
        templates_dir: Optional override for the templates directory.
        static_dir: Optional override for the static assets directory.

    Returns:
        A fully resolved Paths dataclass with data, template, and static paths.

    """
    base = data_dir or os.environ.get("RESUME_DATA_DIR") or PATH_DATA
    base_path = Path(base)

    if data_dir is None:
        data_path = Path(PATH_DATA)
        input_path = Path(PATH_INPUT)
        output_path = Path(PATH_OUTPUT)
    else:
        data_path = base_path
        input_path = base_path / "input"
        output_path = base_path / "output"

    content_path = Path(content_dir) if content_dir is not None else PATH_CONTENT
    templates_path = (
        Path(templates_dir) if templates_dir is not None else content_path / "templates"
    )
    static_path = (
        Path(static_dir) if static_dir is not None else content_path / "static"
    )

    return Paths(
        data=data_path,
        input=input_path,
        output=output_path,
        content=content_path,
        templates=templates_path,
        static=static_path,
    )


# Files
FILE_DEFAULT = "sample_1"
