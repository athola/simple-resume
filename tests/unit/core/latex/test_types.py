"""Tests for LaTeX data types."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.types import (
    Block,
    LatexEntry,
    LatexSection,
    ListBlock,
    ParagraphBlock,
)


class TestParagraphBlock:
    """Tests for ParagraphBlock TypedDict."""

    def test_paragraph_block_structure(self) -> None:
        """Test that ParagraphBlock has correct structure."""
        block: ParagraphBlock = {
            "kind": "paragraph",
            "text": "This is a paragraph with \\textbf{bold} text.",
        }
        assert block["kind"] == "paragraph"
        assert "bold" in block["text"]


class TestListBlock:
    """Tests for ListBlock TypedDict."""

    def test_itemize_block(self) -> None:
        """Test itemize (bullet) list block."""
        block: ListBlock = {
            "kind": "itemize",
            "items": ["First item", "Second item", "Third item"],
        }
        assert block["kind"] == "itemize"
        assert len(block["items"]) == 3

    def test_enumerate_block(self) -> None:
        """Test enumerate (numbered) list block."""
        block: ListBlock = {
            "kind": "enumerate",
            "items": ["First", "Second", "Third"],
        }
        assert block["kind"] == "enumerate"
        assert len(block["items"]) == 3

    def test_empty_items(self) -> None:
        """Test list block with empty items."""
        block: ListBlock = {"kind": "itemize", "items": []}
        assert block["items"] == []


class TestBlock:
    """Tests for Block union type."""

    def test_block_can_be_paragraph(self) -> None:
        """Test that Block can be a ParagraphBlock."""
        block: Block = {"kind": "paragraph", "text": "Test"}
        assert block["kind"] == "paragraph"

    def test_block_can_be_list(self) -> None:
        """Test that Block can be a ListBlock."""
        block: Block = {"kind": "itemize", "items": ["Test"]}
        assert block["kind"] == "itemize"


class TestLatexEntry:
    """Tests for LatexEntry dataclass."""

    def test_minimal_entry(self) -> None:
        """Test entry with minimal required fields."""
        entry = LatexEntry(
            title="Software Engineer",
            subtitle=None,
            date_range=None,
            blocks=[],
        )
        assert entry.title == "Software Engineer"
        assert entry.subtitle is None
        assert entry.date_range is None
        assert entry.blocks == []

    def test_full_entry(self) -> None:
        """Test entry with all fields populated."""
        blocks: list[Block] = [
            {"kind": "paragraph", "text": "Led team of engineers"},
            {"kind": "itemize", "items": ["Task 1", "Task 2"]},
        ]
        entry = LatexEntry(
            title="Senior Software Engineer",
            subtitle="Tech Corp",
            date_range="2020 -- 2023",
            blocks=blocks,
        )
        assert entry.title == "Senior Software Engineer"
        assert entry.subtitle == "Tech Corp"
        assert entry.date_range == "2020 -- 2023"
        assert len(entry.blocks) == 2

    def test_entry_is_frozen(self) -> None:
        """Test that LatexEntry is immutable."""
        entry = LatexEntry(title="Test", subtitle=None, date_range=None, blocks=[])
        with pytest.raises(AttributeError):
            entry.title = "Modified"  # type: ignore[misc]


class TestLatexSection:
    """Tests for LatexSection dataclass."""

    def test_empty_section(self) -> None:
        """Test section with no entries."""
        section = LatexSection(title="Education", entries=[])
        assert section.title == "Education"
        assert section.entries == []

    def test_section_with_entries(self) -> None:
        """Test section with multiple entries."""
        entries = [
            LatexEntry("Degree 1", None, "2020", []),
            LatexEntry("Degree 2", "University", "2015 -- 2019", []),
        ]
        section = LatexSection(title="Education", entries=entries)
        assert section.title == "Education"
        assert len(section.entries) == 2

    def test_section_is_frozen(self) -> None:
        """Test that LatexSection is immutable."""
        section = LatexSection(title="Test", entries=[])
        with pytest.raises(AttributeError):
            section.title = "Modified"  # type: ignore[misc]
