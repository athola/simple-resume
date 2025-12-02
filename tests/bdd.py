"""Lightweight helpers for writing Given/When/Then style tests.

These helpers are intentionally minimal: they record the narrative for a
scenario and expose convenience methods so each test can document the
context, trigger, and expected outcome. They do not alter pytest's control
flow, but they keep the structure consistent and self-documenting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    """BDD-style scenario recorder used inside tests."""

    name: str
    givens: list[str] = field(default_factory=list)
    whens: list[str] = field(default_factory=list)
    thens: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def given(self, clause: str) -> None:
        self.givens.append(clause)

    def when(self, clause: str) -> None:
        self.whens.append(clause)

    def then(self, clause: str) -> None:
        self.thens.append(clause)

    def background(self, **context: Any) -> None:
        """Store reusable context variables for the scenario."""

        self.context.update(context)

    def note(self, clause: str) -> None:
        """Capture additional observational notes."""

        self.notes.append(clause)

    def expect(self, condition: bool, message: str = "Expectation failed") -> None:
        """Assert ``condition`` and raise with a scenario summary if it is false."""

        if not condition:
            raise AssertionError(f"{message}\n\n{self.summary()}")

    def fail(self, message: str) -> None:
        """Unconditionally fail the scenario with a formatted summary."""

        raise AssertionError(f"{message}\n\n{self.summary()}")

    def summary(self) -> str:
        """Render the scenario narrative as a formatted string."""

        lines = [f"Scenario: {self.name}"]
        for title, items in (
            ("Given", self.givens),
            ("When", self.whens),
            ("Then", self.thens),
            ("Notes", self.notes),
        ):
            if items:
                lines.append(f"{title}:")
                lines.extend([f"  - {item}" for item in items])
        if self.context:
            lines.append("Context:")
            for key, value in self.context.items():
                lines.append(f"  - {key}: {value!r}")
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover - trivial wrapper
        """Return the formatted summary for convenient printing."""
        return self.summary()

    def case(
        self,
        description: str | None = None,
        *,
        given: str | list[str] | None = None,
        when: str | list[str] | None = None,
        then: str | list[str] | None = None,
    ) -> None:
        """Register a scenario with optional Given/When/Then clauses."""

        desc = description if description is not None else ""
        if desc:
            self.note(desc)

        def _record(clauses: str | list[str] | None, writer) -> None:
            if clauses is None:
                return
            if isinstance(clauses, str):
                writer(clauses)
            else:
                for clause in clauses:
                    writer(clause)

        _record(given, self.given)
        _record(when, self.when)
        _record(then, self.then)


def scenario(name: str) -> Scenario:
    """Create a scenario helper to emphasize intent inside tests."""

    return Scenario(name=name)
