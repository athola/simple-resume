"""Tests for core/skills.py - skill formatting functions."""

from __future__ import annotations

from simple_resume.core.skills import format_skill_groups
from tests.bdd import Scenario


class TestFormatSkillGroups:
    """Tests for format_skill_groups function."""

    def test_none_input_returns_empty_list(self, story: Scenario) -> None:
        """Test that None input returns empty list."""
        story.given("None as skills input")
        story.when("formatting skill groups")
        result = format_skill_groups(None)
        assert result == []

    def test_simple_string_input(self, story: Scenario) -> None:
        """Test single string input."""
        story.given("a single string skill 'Python'")
        story.when("formatting skill groups")
        result = format_skill_groups("Python")
        assert len(result) == 1
        assert result[0]["title"] is None
        items = result[0]["items"]
        assert isinstance(items, list)
        assert "Python" in items

    def test_list_of_strings(self, story: Scenario) -> None:
        """Test list of string skills."""
        story.given("a list of skill strings")
        story.when("formatting skill groups")
        result = format_skill_groups(["Python", "JavaScript", "Go"])
        assert len(result) == 1
        assert result[0]["title"] is None
        assert result[0]["items"] == ["Python", "JavaScript", "Go"]

    def test_dict_with_categories(self, story: Scenario) -> None:
        """Test dict with skill categories."""
        story.given("a dictionary with categorized skills")
        story.when("formatting skill groups")
        skill_data = {
            "Programming": ["Python", "JavaScript"],
            "Databases": ["PostgreSQL", "Redis"],
        }
        result = format_skill_groups(skill_data)
        assert len(result) == 2

    def test_list_with_dict_entries(self, story: Scenario) -> None:
        """Test list containing dict entries."""
        story.given("a list of dictionaries with skill categories")
        story.when("formatting skill groups")
        skill_data = [
            {"Programming": ["Python", "JavaScript"]},
            {"Databases": ["PostgreSQL"]},
        ]
        result = format_skill_groups(skill_data)
        assert len(result) == 2

    def test_list_with_mixed_content(self, story: Scenario) -> None:
        """Test list with both dict and non-dict entries."""
        story.given("a list with both dict and string entries")
        story.when("formatting skill groups")
        skill_data = [
            {"Programming": ["Python"]},
            "Standalone Skill",  # Non-dict entry
        ]
        result = format_skill_groups(skill_data)
        # Should have two groups: one for Programming, one for standalone
        assert len(result) == 2
        # One should have title None (the standalone skill)
        none_groups = [g for g in result if g["title"] is None]
        assert len(none_groups) == 1

    def test_empty_list_returns_empty_list(self, story: Scenario) -> None:
        """Test empty list input returns empty list."""
        story.given("an empty list as skills input")
        story.when("formatting skill groups")
        result = format_skill_groups([])
        assert result == []

    def test_empty_dict_returns_empty_list(self, story: Scenario) -> None:
        """Test empty dict input returns empty list."""
        story.given("an empty dictionary as skills input")
        story.when("formatting skill groups")
        result = format_skill_groups({})
        assert result == []

    def test_dict_with_none_value(self, story: Scenario) -> None:
        """Test dict with None value for items."""
        story.given("a dictionary with None value for one category")
        story.when("formatting skill groups")
        skill_data = {
            "Programming": None,  # None value should be coerced to empty list
            "Databases": ["PostgreSQL"],
        }
        result = format_skill_groups(skill_data)
        # Should only have one group (Databases), Programming is skipped
        assert len(result) == 1
        assert result[0]["title"] == "Databases"
