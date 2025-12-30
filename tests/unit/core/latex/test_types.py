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
from tests.bdd import Scenario


class TestParagraphBlock:
    """Tests for ParagraphBlock TypedDict."""

    def test_paragraph_block_structure(self, story: Scenario) -> None:
        """Test that ParagraphBlock has correct structure."""
        story.given("a ParagraphBlock TypedDict with kind and text fields")
        story.when("accessing the block fields")
        block: ParagraphBlock = {
            "kind": "paragraph",
            "text": "This is a paragraph with \\textbf{bold} text.",
        }
        assert block["kind"] == "paragraph"
        assert "bold" in block["text"]


class TestListBlock:
    """Tests for ListBlock TypedDict."""

    def test_itemize_block(self, story: Scenario) -> None:
        """Test itemize (bullet) list block."""
        story.given("a ListBlock with kind 'itemize' and three items")
        story.when("accessing the block fields")
        block: ListBlock = {
            "kind": "itemize",
            "items": ["First item", "Second item", "Third item"],
        }
        assert block["kind"] == "itemize"
        assert len(block["items"]) == 3

    def test_enumerate_block(self, story: Scenario) -> None:
        """Test enumerate (numbered) list block."""
        story.given("a ListBlock with kind 'enumerate' and three items")
        story.when("accessing the block fields")
        block: ListBlock = {
            "kind": "enumerate",
            "items": ["First", "Second", "Third"],
        }
        assert block["kind"] == "enumerate"
        assert len(block["items"]) == 3

    def test_empty_items(self, story: Scenario) -> None:
        """Test list block with empty items."""
        story.given("a ListBlock with an empty items list")
        story.when("accessing the items field")
        block: ListBlock = {"kind": "itemize", "items": []}
        assert block["items"] == []


class TestBlock:
    """Tests for Block union type."""

    def test_block_can_be_paragraph(self, story: Scenario) -> None:
        """Test that Block can be a ParagraphBlock."""
        story.given("a Block typed as ParagraphBlock")
        story.when("checking the kind field")
        block: Block = {"kind": "paragraph", "text": "Test"}
        assert block["kind"] == "paragraph"

    def test_block_can_be_list(self, story: Scenario) -> None:
        """Test that Block can be a ListBlock."""
        story.given("a Block typed as ListBlock")
        story.when("checking the kind field")
        block: Block = {"kind": "itemize", "items": ["Test"]}
        assert block["kind"] == "itemize"


class TestLatexEntry:
    """Tests for LatexEntry dataclass."""

    def test_minimal_entry(self, story: Scenario) -> None:
        """Test entry with minimal required fields."""
        story.given("minimal fields for a LatexEntry (only title)")
        story.when("creating the LatexEntry dataclass")
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

    def test_full_entry(self, story: Scenario) -> None:
        """Test entry with all fields populated."""
        story.given("all fields populated for a LatexEntry")
        story.when("creating the LatexEntry dataclass")
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

    def test_entry_is_frozen(self, story: Scenario) -> None:
        """Test that LatexEntry is immutable."""
        story.given("a frozen LatexEntry dataclass instance")
        story.when("attempting to modify a field")
        entry = LatexEntry(title="Test", subtitle=None, date_range=None, blocks=[])
        with pytest.raises(AttributeError):
            entry.title = "Modified"  # type: ignore[misc]


class TestLatexSection:
    """Tests for LatexSection dataclass."""

    def test_empty_section(self, story: Scenario) -> None:
        """Test section with no entries."""
        story.given("a LatexSection with no entries")
        story.when("creating the section")
        section = LatexSection(title="Education", entries=[])
        assert section.title == "Education"
        assert section.entries == []

    def test_section_with_entries(self, story: Scenario) -> None:
        """Test section with multiple entries."""
        story.given("multiple LatexEntry instances")
        story.when("creating a LatexSection with those entries")
        entries = [
            LatexEntry("Degree 1", None, "2020", []),
            LatexEntry("Degree 2", "University", "2015 -- 2019", []),
        ]
        section = LatexSection(title="Education", entries=entries)
        assert section.title == "Education"
        assert len(section.entries) == 2

    def test_section_is_frozen(self, story: Scenario) -> None:
        """Test that LatexSection is immutable."""
        story.given("a frozen LatexSection dataclass instance")
        story.when("attempting to modify the title field")
        section = LatexSection(title="Test", entries=[])
        with pytest.raises(AttributeError):
            section.title = "Modified"  # type: ignore[misc]
