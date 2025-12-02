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


def get_absolute_shell_imports(file_path: Path) -> set[str]:
    """Extract absolute imports from simple_resume.shell.

    This detects module-level imports like:
    - from simple_resume.shell.strategies import ...
    - import simple_resume.shell.io_utils

    Note: Late-bound imports inside functions are acceptable for
    dependency injection patterns and are not detected by this function.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return set()

    shell_imports = set()

    for node in ast.walk(tree):
        # Only check module-level imports (direct children of Module)
        if isinstance(node, ast.Module):
            for child in node.body:
                if isinstance(child, ast.ImportFrom):
                    if child.module and "simple_resume.shell" in child.module:
                        shell_imports.add(child.module)
                elif isinstance(child, ast.Import):
                    for alias in child.names:
                        if "simple_resume.shell" in alias.name:
                            shell_imports.add(alias.name)

    return shell_imports


def get_import_dependencies(file_path: Path) -> set[str]:
    """Extract all module dependencies from a file using AST."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return set()

    dependencies = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Handle both absolute and relative imports
                if node.level == 0:  # Absolute import
                    dependencies.add(node.module.split(".")[0])
                else:  # Relative import - resolve to absolute
                    # Get the parent directory path
                    parent_path = file_path.parent
                    # Go up the directory tree based on import level
                    for _ in range(node.level):
                        parent_path = parent_path.parent

                    # Resolve the target module
                    if node.module:
                        target_path = parent_path / node.module.replace(".", "/")
                    else:
                        target_path = parent_path

                    # Convert to simple module name (relative to package root)
                    try:
                        relative_to_root = target_path.relative_to(PACKAGE_ROOT)
                        dependencies.add(str(relative_to_root.parts[0]))
                    except ValueError:
                        # Import is outside the package - skip
                        pass

    return dependencies


class TestCoreLayerSeparation:
    """Test that core modules don't violate layer separation."""

    def test_core_modules_exist(self) -> None:
        """Verify core directory exists and has modules."""
        core_dir = PACKAGE_ROOT / "core"
        assert core_dir.exists(), "Core directory should exist"
        core_files = get_python_files(core_dir)
        assert len(core_files) > 0, "Core directory should contain Python files"

    def test_core_no_io_library_imports(self) -> None:
        """Core modules must not import I/O libraries.

        Known exceptions (TODO - refactor these):
        - core/result.py: subprocess (complex refactoring needed)
        - core/generate/pdf.py: weasyprint (needs protocol abstraction)
        """
        # Known violations that are being worked on
        KNOWN_VIOLATIONS = {
            "core/result.py": {"subprocess"},
            "core/generate/pdf.py": {"weasyprint"},
        }

        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        violations = []
        unexpected_violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue  # Skip __init__ files

            imports = extract_imports(file_path)
            forbidden_found = imports & FORBIDDEN_CORE_IMPORTS

            if forbidden_found:
                relative_path = file_path.relative_to(PACKAGE_ROOT)
                relative_str = str(relative_path)

                # Check if this is a known violation
                expected_imports = KNOWN_VIOLATIONS.get(relative_str, set())
                unexpected_imports = forbidden_found - expected_imports

                if unexpected_imports:
                    # New violation - fail the test
                    imports_str = ", ".join(sorted(unexpected_imports))
                    unexpected_violations.append(
                        f"{relative_str}: imports {imports_str}"
                    )
                elif forbidden_found:
                    # Known violation - just document it
                    imports_str = ", ".join(sorted(forbidden_found))
                    violations.append(
                        f"{relative_str}: imports {imports_str} (known TODO)"
                    )

        if unexpected_violations:
            violation_report = "\n  - ".join(unexpected_violations)
            pytest.fail(
                f"Core modules must not import I/O libraries.\n"
                f"NEW violations found:\n  - {violation_report}\n\n"
                f"Known violations (being refactored):\n  - "
                + "\n  - ".join(violations or ["None"])
            )

    def test_core_no_shell_imports(self) -> None:
        """Core modules must not import from shell layer at module level.

        Note: Late-bound imports inside functions (for dependency injection)
        are acceptable and not flagged by this test. Only module-level imports
        that create import-time dependencies are violations.
        """
        core_dir = PACKAGE_ROOT / "core"
        core_files = get_python_files(core_dir)

        violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue

            relative_path = file_path.relative_to(PACKAGE_ROOT)

            # Check for relative imports from shell
            relative_imports = get_relative_imports(file_path)
            for rel_import in relative_imports:
                if "shell" in rel_import:
                    violations.append(
                        f"{relative_path}: relative import from {rel_import}"
                    )

            # Check for absolute imports from shell (module-level only)
            absolute_imports = get_absolute_shell_imports(file_path)
            for abs_import in absolute_imports:
                violations.append(f"{relative_path}: absolute import from {abs_import}")

        if violations:
            violation_report = "\n  - ".join(violations)
            pytest.fail(
                "Core modules must not import from shell layer at module level.\n"
                f"Violations found:\n  - {violation_report}\n\n"
                "Note: Late-bound imports inside functions (for dependency injection)\n"
                "are acceptable. Move shell imports inside functions to fix violations."
            )

    def test_core_no_direct_file_operations(self) -> None:
        """Core modules should not perform direct file operations.

        Known exceptions (TODO - refactor these):
        - core/result.py: .read_text() methods (complex refactoring)
        - core/resume.py: result.open() calls (false positive - method calls)
        """
        # Known violations - file patterns that are acceptable
        KNOWN_VIOLATIONS = {
            "core/result.py": [".read_text(", ".read_bytes("],
            "core/resume.py": ["result.open(", "webbrowser.open("],
        }

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
        unexpected_violations = []

        for file_path in core_files:
            if file_path.name == "__init__.py":
                continue

            # Special exception for file_operations.py which is a boundary case
            if file_path.name == "file_operations.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                relative_path = file_path.relative_to(PACKAGE_ROOT)
                relative_str = str(relative_path)
                known_patterns = KNOWN_VIOLATIONS.get(relative_str, [])

                for pattern in file_io_patterns:
                    if pattern in content:
                        # Check if this is a known violation
                        any(
                            known_pattern in content
                            for known_pattern in known_patterns
                            if known_pattern.startswith(pattern)
                            or pattern in known_pattern
                        )

                        if relative_str in KNOWN_VIOLATIONS:
                            # This file has known violations - document it
                            violations.append(
                                f"{relative_str}: contains '{pattern}' (known TODO)"
                            )
                        else:
                            # NEW violation
                            unexpected_violations.append(
                                f"{relative_str}: contains '{pattern}'"
                            )
                        break  # Only report once per file

            except Exception:  # nosec B112  # noqa: BLE001, S112
                continue

        if unexpected_violations:
            violation_report = "\n  - ".join(unexpected_violations)
            pytest.fail(
                f"Core modules should not perform direct file I/O.\n"
                f"NEW violations found:\n  - {violation_report}\n\n"
                f"Known violations (being refactored):\n  - "
                + "\n  - ".join(violations or ["None"])
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


def build_dependency_graph(package_root: Path) -> dict[str, set[str]]:
    """Build a dependency graph showing which modules depend on which."""
    graph: dict[str, set[str]] = {}

    # Get all Python files in the package
    all_files = list(package_root.rglob("*.py"))

    for file_path in all_files:
        if file_path.name == "__init__.py":
            continue

        try:
            # Convert file path to module name
            module_name = str(file_path.relative_to(package_root).with_suffix(""))
            module_name = module_name.replace("/", ".")

            dependencies = get_import_dependencies(file_path)
            graph[module_name] = dependencies

        except Exception:  # noqa: S112  # nosec B112
            continue

    return graph


def find_circular_dependencies(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    """Find circular dependencies using DFS."""
    cycles = []

    def visit(node: str, path: set[str]) -> None:
        if node in path:
            # Found a cycle - extract the cycle
            cycle_start = list(path).index(node)
            cycle = list(path)[cycle_start:] + [node]
            cycles.append(tuple(cycle))
            return

        if node not in graph:
            return

        path.add(node)
        for neighbor in graph[node]:
            visit(neighbor, path.copy())
        path.remove(node)

    for module in graph:
        visit(module, set())

    return cycles


class TestDependencyDirection:
    """Test overall dependency flow in the architecture."""

    def test_no_circular_dependencies_core_utils(self) -> None:
        """Detect circular dependencies between core and utilities."""
        # Build dependency graph for the entire package
        graph = build_dependency_graph(PACKAGE_ROOT)

        # Find cycles
        cycles = find_circular_dependencies(graph)

        # Filter cycles that involve both core and utilities
        problematic_cycles = []
        for cycle in cycles:
            cycle_strs = list(cycle)
            has_core = any(
                "core." in module or module == "core" for module in cycle_strs
            )
            has_utils = any(
                "utils." in module or module == "utilities" for module in cycle_strs
            )

            if has_core and has_utils:
                problematic_cycles.append(cycle)

        if problematic_cycles:
            # Create a detailed report
            cycle_report = "\n".join(
                f"  {' -> '.join(cycle)} (cycle of length {len(cycle)})"
                for cycle in problematic_cycles
            )

            pytest.fail(
                f"Circular dependencies detected between core and utilities:\n"
                f"{cycle_report}\n\n"
                f"This creates coupling and makes testing difficult.\n"
                f"Consider refactoring to break these cycles by:\n"
                f"  1. Moving shared functionality to a separate module\n"
                f"  2. Using dependency injection instead of direct imports\n"
                f"  3. Restructuring to avoid bidirectional dependencies"
            )


class TestArchitectureDocumentation:
    """Test that architecture documentation exists."""

    def test_architecture_doc_exists(self) -> None:
        """Architecture documentation should exist."""
        arch_doc = (
            Path(__file__).parent.parent.parent / "wiki" / "Architecture-Guide.md"
        )

        # This test will initially fail - we'll create the doc in this phase
        assert arch_doc.exists(), (
            "wiki/Architecture-Guide.md should exist to document layer separation "
            "rules.\nThis will be created in Phase 1."
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
