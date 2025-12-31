"""Tests for core/file_operations.py - pure file discovery functions."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.file_operations import (
    find_yaml_files,
    get_resume_name_from_path,
    iterate_yaml_files,
)
from tests.bdd import Scenario


class TestFindYamlFiles:
    """Tests for find_yaml_files function."""

    def test_finds_yaml_and_yml_files(self, tmp_path: Path, story: Scenario) -> None:
        """Test finding both .yaml and .yml files."""
        story.given("a directory with .yaml, .yml, and other files")
        story.when("finding yaml files")
        (tmp_path / "resume1.yaml").write_text("config: {}")
        (tmp_path / "resume2.yml").write_text("config: {}")
        (tmp_path / "readme.txt").write_text("not yaml")

        result = find_yaml_files(tmp_path)

        assert len(result) == 2
        assert any(f.name == "resume1.yaml" for f in result)
        assert any(f.name == "resume2.yml" for f in result)

    def test_returns_empty_list_for_nonexistent_dir(self, story: Scenario) -> None:
        """Test returns empty list when directory doesn't exist."""
        story.given("a nonexistent directory path")
        story.when("finding yaml files")
        nonexistent = Path("/nonexistent/directory")
        result = find_yaml_files(nonexistent)
        assert result == []

    def test_filters_by_pattern(self, tmp_path: Path, story: Scenario) -> None:
        """Test filtering files by pattern."""
        story.given("a directory with multiple yaml files")
        story.when("finding yaml files with a pattern filter")
        (tmp_path / "john.yaml").write_text("config: {}")
        (tmp_path / "jane.yaml").write_text("config: {}")
        (tmp_path / "sample.yaml").write_text("config: {}")

        result = find_yaml_files(tmp_path, pattern="john")

        assert len(result) == 1
        assert result[0].name == "john.yaml"

    def test_sorts_results(self, tmp_path: Path, story: Scenario) -> None:
        """Test results are sorted."""
        story.given("a directory with unsorted yaml files")
        story.when("finding yaml files")
        (tmp_path / "zebra.yaml").write_text("config: {}")
        (tmp_path / "apple.yaml").write_text("config: {}")
        (tmp_path / "middle.yaml").write_text("config: {}")

        result = find_yaml_files(tmp_path)

        names = [f.name for f in result]
        assert names == sorted(names)


class TestIterateYamlFiles:
    """Tests for iterate_yaml_files generator function."""

    def test_yields_yaml_files(self, tmp_path: Path, story: Scenario) -> None:
        """Test yielding YAML files."""
        story.given("a directory with yaml and yml files")
        story.when("iterating yaml files")
        (tmp_path / "resume1.yaml").write_text("config: {}")
        (tmp_path / "resume2.yml").write_text("config: {}")

        result = list(iterate_yaml_files(tmp_path))

        assert len(result) == 2
        assert all(isinstance(f, Path) for f in result)

    def test_is_generator(self, tmp_path: Path, story: Scenario) -> None:
        """Test that iterate_yaml_files returns a generator."""
        story.given("a directory with a yaml file")
        story.when("calling iterate_yaml_files")
        (tmp_path / "test.yaml").write_text("config: {}")

        result = iterate_yaml_files(tmp_path)

        # Verify it's a generator (has __next__)
        assert hasattr(result, "__next__")

    def test_yields_with_pattern(self, tmp_path: Path, story: Scenario) -> None:
        """Test yielding files matching pattern."""
        story.given("a directory with multiple yaml files")
        story.when("iterating yaml files with a pattern filter")
        (tmp_path / "john.yaml").write_text("config: {}")
        (tmp_path / "jane.yaml").write_text("config: {}")

        result = list(iterate_yaml_files(tmp_path, pattern="john"))

        assert len(result) == 1
        assert result[0].name == "john.yaml"


class TestGetResumeNameFromPath:
    """Tests for get_resume_name_from_path function."""

    def test_extracts_name_from_yaml_path(self, story: Scenario) -> None:
        """Test extracting name from .yaml file."""
        story.given("a path to a .yaml file")
        story.when("extracting the resume name")
        path = Path("/some/dir/john_doe.yaml")
        result = get_resume_name_from_path(path)
        assert result == "john_doe"

    def test_extracts_name_from_yml_path(self, story: Scenario) -> None:
        """Test extracting name from .yml file."""
        story.given("a path to a .yml file")
        story.when("extracting the resume name")
        path = Path("/some/dir/jane_smith.yml")
        result = get_resume_name_from_path(path)
        assert result == "jane_smith"

    def test_extracts_name_with_special_characters(self, story: Scenario) -> None:
        """Test extracting name with underscores and hyphens."""
        story.given("a path with underscores and hyphens in filename")
        story.when("extracting the resume name")
        path = Path("/dir/resume-2024_final.yaml")
        result = get_resume_name_from_path(path)
        assert result == "resume-2024_final"

    def test_extracts_from_relative_path(self, story: Scenario) -> None:
        """Test extracting name from relative path."""
        story.given("a relative path to a yaml file")
        story.when("extracting the resume name")
        path = Path("input/sample.yaml")
        result = get_resume_name_from_path(path)
        assert result == "sample"
