"""Provide utilities for skill data processing and formatting."""

from __future__ import annotations

from typing import Any


def _coerce_items(raw_input: Any) -> list[str]:
    """Return a list of trimmed string items from arbitrary input."""
    if raw_input is None:
        return []
    if isinstance(raw_input, (list, tuple, set)):
        return [str(element).strip() for element in raw_input if str(element).strip()]
    return [str(raw_input).strip()]


def format_skill_groups(
    skill_data: Any,
) -> list[dict[str, list[str] | str | None]]:
    """Normalize skill data into titled groups with string entries."""
    groups: list[dict[str, list[str] | str | None]] = []

    if skill_data is None:
        return groups

    def add_group(title: str | None, items: Any) -> None:
        normalized = [entry for entry in _coerce_items(items) if entry]
        if not normalized:
            return
        groups.append(
            {
                "title": str(title).strip() if title else None,
                "items": normalized,
            }
        )

    if isinstance(skill_data, dict):
        for category_name, items in skill_data.items():
            add_group(str(category_name), items)
        return groups

    if isinstance(skill_data, (list, tuple, set)):
        # Check if all entries are simple strings (not dicts)
        all_simple = all(not isinstance(entry, dict) for entry in skill_data)

        if all_simple:
            # Create a single group with all items
            add_group(None, list(skill_data))
        else:
            # Mixed content: process each entry separately
            for entry in skill_data:
                if isinstance(entry, dict):
                    for category_name, items in entry.items():
                        add_group(str(category_name), items)
                else:
                    add_group(None, entry)
        return groups

    add_group(None, skill_data)
    return groups
