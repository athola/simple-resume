"""Guardrail test to keep core import purity metric current.

Scans all core modules for forbidden imports (I/O libs and shell modules).
Fails if any violations are found. Mirrors the manual snippet documented in
wiki/Architecture-Guide.md to ensure CI and docs stay in sync.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).parent.parent.parent / "src" / "simple_resume"
CORE_DIR = PACKAGE_ROOT / "core"

# Keep list in sync with Architecture-Guide status note
FORBIDDEN = (
    "weasyprint",
    "yaml",
    "requests",
    "urllib",
    "subprocess",
    "simple_resume.shell",
)


def _scan_forbidden_imports(file_path: Path) -> set[str]:
    """Return matching forbidden import prefixes in the given file."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    hits: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [node.module or ""]
        else:
            continue

        for target in targets:
            for forbidden in FORBIDDEN:
                if target == forbidden or target.startswith(forbidden + "."):
                    hits.add(forbidden)
    return hits


def test_core_has_no_forbidden_imports() -> None:
    """All core modules must avoid shell and I/O imports."""
    assert CORE_DIR.exists(), "core directory must exist"
    py_files = list(CORE_DIR.rglob("*.py"))
    assert py_files, "core directory must contain Python files"

    violations = {
        path.relative_to(Path(".")).as_posix(): sorted(_scan_forbidden_imports(path))
        for path in py_files
        if _scan_forbidden_imports(path)
    }

    if violations:
        details = "\n".join(
            f"- {path} -> {', '.join(items)}"
            for path, items in sorted(violations.items())
        )
        pytest.fail(f"Forbidden imports detected in core:\n{details}")
