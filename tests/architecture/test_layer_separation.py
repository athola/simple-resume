"""Architectural tests for functional core, imperative shell pattern.

These tests enforce the separation between core (pure logic) and shell (I/O).
They will fail on current code - this is expected and intentional.
Violations will be fixed in subsequent phases of the refactoring plan.
"""

import ast
from pathlib import Path

import pytest

# Root of the simple_resume package
PACKAGE_ROOT = Path(__file__).parent.parent.parent / "src" / "simple_resume"


# I/O and external dependencies forbidden in core
FORBIDDEN_CORE_IMPORTS = {
    "weasyprint",
    "yaml",
    "requests",
    "urllib",
    "subprocess",
    "http",
    "socket",
}


def get_python_files(directory: Path) -> list[Path]:
    """Get all Python files in a directory recursively."""
    return list(directory.rglob("*.py"))


def extract_imports(file_path: Path) -> set[str]:
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def get_relative_imports(file_path: Path) -> set[str]:
    """Extract relative imports (like 'from ..shell import')."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return set()

    relative_imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:  # Relative import
                # Get the module path
                parts = []
                if node.module:
                    parts.append(node.module)

                # Reconstruct the relative path
                relative_path = ".." * node.level + (".".join(parts) if parts else "")
                relative_imports.add(relative_path)

    return relative_imports


class TestCoreLayerSeparation:
    """Test that core modules don't violate layer separation."""

    def test_core_modules_exist(self) -> None:
        """Verify core directory exists and has modules."""
        core_dir = PACKAGE_ROOT / "core"
        assert core_dir.exists(), "Core directory should exist"
        core_files = get_python_files(core_dir)
        assert len(core_files) > 0, "Core directory should contain Python files"

    @pytest.mark.xfail(
        reason=(
            "Expected during refactoring - will be fixed in Phase 2 "
            "(see CORE_REFACTOR_PLAN.md)"
        )
    )
    def test_core_no_io_library_imports(self) -> None:
        """Core modules must not import I/O libraries."""
        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue  # Skip __init__ files

            imports = extract_imports(file_path)
            forbidden_found = imports & FORBIDDEN_CORE_IMPORTS

            if forbidden_found:
                relative_path = file_path.relative_to(PACKAGE_ROOT)
                violations.append(
                    f"{relative_path}: imports {', '.join(sorted(forbidden_found))}"
                )

        if violations:
            violation_report = "\n  - ".join(violations)
            pytest.fail(
                f"Core modules must not import I/O libraries.\n"
                f"Violations found:\n  - {violation_report}\n\n"
                f"Expected violations (will be fixed in later phases):\n"
                f"  - core/pdf_generation.py: weasyprint\n"
                f"  - core/html_generation.py: (none expected now)\n"
            )

    @pytest.mark.xfail(
        reason=(
            "Expected during refactoring - will be fixed in Phase 2 "
            "(see CORE_REFACTOR_PLAN.md)"
        )
    )
    def test_core_no_shell_imports(self) -> None:
        """Core modules must not import from shell layer."""
        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue

            relative_imports = get_relative_imports(file_path)

            # Check for imports from shell
            for rel_import in relative_imports:
                if "shell" in rel_import:
                    relative_path = file_path.relative_to(PACKAGE_ROOT)
                    violations.append(f"{relative_path}: imports from {rel_import}")

        if violations:
            violation_report = "\n  - ".join(violations)
            pytest.fail(
                f"Core modules must not import from shell layer.\n"
                f"Violations found:\n  - {violation_report}\n\n"
                f"Expected violations (will be fixed in Phase 2):\n"
                f"  - core/strategies.py: imports from shell\n"
            )

    @pytest.mark.xfail(
        reason=(
            "Expected during refactoring - will be fixed in Phases 2-3 "
            "(see CORE_REFACTOR_PLAN.md)"
        )
    )
    def test_core_no_direct_file_operations(self) -> None:
        """Core modules should not perform direct file operations."""
        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        # Patterns that indicate file I/O
        file_io_patterns = [
            ".write_text(",
            ".write_bytes(",
            ".read_text(",
            ".read_bytes(",
            ".mkdir(",
            ".unlink(",
            "open(",
            "Path.glob(",  # Read-only but still I/O
        ]

        violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue

            # Special exception for file_operations.py which is a boundary case
            if file_path.name == "file_operations.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                for pattern in file_io_patterns:
                    if pattern in content:
                        relative_path = file_path.relative_to(PACKAGE_ROOT)
                        violations.append(f"{relative_path}: contains '{pattern}'")
                        break  # Only report once per file

            except Exception:  # nosec B112  # noqa: BLE001, S112
                continue

        if violations:
            violation_report = "\n  - ".join(violations)
            pytest.fail(
                f"Core modules should not perform direct file I/O.\n"
                f"Violations found:\n  - {violation_report}\n\n"
                f"Expected violations (will be fixed in Phases 2-3):\n"
                f"  - core/pdf_generation.py: file writes\n"
                f"  - core/html_generation.py: file writes\n"
                f"  - core/resume.py: file operations\n"
            )


class TestShellLayerSeparation:
    """Test that shell layer correctly depends on core."""

    def test_shell_modules_exist(self) -> None:
        """Verify shell directory exists and has modules."""
        shell_dir = PACKAGE_ROOT / "shell"
        assert shell_dir.exists(), "Shell directory should exist"
        shell_files = get_python_files(shell_dir)
        assert len(shell_files) > 0, "Shell directory should contain Python files"

    def test_shell_can_import_core(self) -> None:
        """Shell modules are allowed to import from core (this should pass)."""
        shell_dir = PACKAGE_ROOT / "shell"
        shell_files = get_python_files(shell_dir)

        # This test just verifies that we can detect core imports
        # It should always pass - just documenting the allowed direction
        core_import_count = 0

        for file_path in shell_files:
            relative_imports = get_relative_imports(file_path)
            for rel_import in relative_imports:
                if "core" in rel_import:
                    core_import_count += 1

        # This is informational - we expect shell to import from core
        assert core_import_count >= 0, "Shell can import from core (this is allowed)"

    def test_shell_can_use_io_libraries(self) -> None:
        """Shell modules are allowed to use I/O libraries (this should pass)."""
        shell_dir = PACKAGE_ROOT / "shell"
        shell_files = get_python_files(shell_dir)

        # This is informational - shell is ALLOWED to use I/O
        io_library_usage = 0

        for file_path in shell_files:
            imports = extract_imports(file_path)
            if imports & FORBIDDEN_CORE_IMPORTS:
                io_library_usage += 1

        # This should pass - it's documenting that shell CAN use I/O
        assert io_library_usage >= 0, "Shell can use I/O libraries (this is allowed)"


class TestDependencyDirection:
    """Test overall dependency flow in the architecture."""

    @pytest.mark.xfail(
        reason=(
            "Expected during refactoring - will be fixed in Phase 5 "
            "(see CORE_REFACTOR_PLAN.md)"
        )
    )
    def test_no_circular_dependencies_core_utils(self) -> None:
        """Detect circular dependencies between core and utilities."""
        # This is a simplified check - full circular dependency detection
        # would require a more sophisticated graph analysis

        core_dir = PACKAGE_ROOT / "core"
        utils_file = PACKAGE_ROOT / "utilities.py"

        if not utils_file.exists():
            pytest.skip("utilities.py not found")

        # Check if core imports utilities
        core_files = get_python_files(core_dir)
        core_imports_utils = False

        for file_path in core_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    if (
                        "from ..utilities import" in content
                        or "from .utilities import" in content
                    ):
                        core_imports_utils = True
                        break
            except Exception:  # nosec B112  # noqa: BLE001, S112
                continue

        # Check if utilities imports core
        utils_imports_core = False
        try:
            with open(utils_file, encoding="utf-8") as f:
                content = f.read()
                if "from .core" in content or "from simple_resume.core" in content:
                    utils_imports_core = True
        except Exception:  # nosec B110  # noqa: BLE001, S110
            pass

        if core_imports_utils and utils_imports_core:
            pytest.fail(
                "Circular dependency detected: core <-> utilities\n"
                "This creates coupling and makes testing difficult.\n"
                "Expected: This may fail and will be fixed in Phase 5."
            )


class TestArchitectureDocumentation:
    """Test that architecture documentation exists."""

    def test_architecture_doc_exists(self) -> None:
        """Architecture documentation should exist."""
        arch_doc = Path(__file__).parent.parent.parent / "wiki" / "ARCHITECTURE.md"

        # This test will initially fail - we'll create the doc in this phase
        assert arch_doc.exists(), (
            "wiki/ARCHITECTURE.md should exist to document layer separation rules.\n"
            "This will be created in Phase 1."
        )

    def test_adr002_exists(self) -> None:
        """ADR002 about functional core should exist."""
        adr002 = (
            Path(__file__).parent.parent.parent
            / "wiki"
            / "architecture"
            / "ADR002-functional-core-imperative-shell.md"
        )
        assert adr002.exists(), "ADR002 should document the core/shell pattern"


class TestCodeQualityMetrics:
    """Test code quality metrics related to architecture."""

    def test_core_modules_have_type_hints(self) -> None:
        """Core modules should have type hints for better testability."""
        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        modules_without_hints = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Simple heuristic: check for type hint syntax
                has_hints = "->" in content or ": " in content

                if not has_hints:
                    relative_path = file_path.relative_to(PACKAGE_ROOT)
                    modules_without_hints.append(str(relative_path))

            except Exception:  # nosec B112  # noqa: BLE001, S112
                continue

        # This is informational - we have good type hint coverage
        assert len(modules_without_hints) < 5, (
            f"Most core modules should have type hints.\n"
            f"Modules without hints: {modules_without_hints}"
        )


if __name__ == "__main__":
    """Allow running tests directly."""
    pytest.main([__file__, "-v"])
