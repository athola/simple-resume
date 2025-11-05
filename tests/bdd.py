"""Lightweight helpers for writing Given/When/Then style tests.

These helpers are intentionally minimal: they record the narrative for a
scenario and expose convenience methods so each test can document the
context, trigger, and expected outcome. They do not alter pytest's control
flow, but they keep the structure consistent and self-documenting.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scenario:
    """BDD-style scenario recorder used inside tests."""

    name: str
    givens: list[str] = field(default_factory=list)
    whens: list[str] = field(default_factory=list)
    thens: list[str] = field(default_factory=list)

    def given(self, clause: str) -> None:
        self.givens.append(clause)

    def when(self, clause: str) -> None:
        self.whens.append(clause)

    def then(self, clause: str) -> None:
        self.thens.append(clause)


def scenario(name: str) -> Scenario:
    """Create a scenario helper to emphasize intent inside tests."""

    return Scenario(name=name)
