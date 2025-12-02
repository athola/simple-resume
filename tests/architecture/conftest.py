"""Pytest tweaks for architecture-only runs."""

from __future__ import annotations

from collections.abc import Sequence


def _only_architecture_selected(args: Sequence[str]) -> bool:
    """Return True if pytest was invoked only on architecture tests."""
    return bool(args) and all(arg.startswith("tests/architecture") for arg in args)


def pytest_configure(config) -> None:  # type: ignore[override]
    """Relax coverage threshold when running architecture suite alone."""
    if _only_architecture_selected(getattr(config, "args", ())):
        if hasattr(config.option, "cov_fail_under"):
            config.option.cov_fail_under = 0
