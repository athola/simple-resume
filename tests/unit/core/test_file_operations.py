"""Tests for core/file_operations.py - pure file discovery functions."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.file_operations import (
    find_yaml_files,
    get_resume_name_from_path,
    iterate_yaml_files,
)


class TestFindYamlFiles:
    """Tests for find_yaml_files function."""

    def test_finds_yaml_and_yml_files(self, tmp_path: Path) -> None:
        """Test finding both .yaml and .yml files."""
        (tmp_path / "resume1.yaml").write_text("config: {}")
        (tmp_path / "resume2.yml").write_text("config: {}")
        (tmp_path / "readme.txt").write_text("not yaml")

        result = find_yaml_files(tmp_path)

        assert len(result) == 2
        assert any(f.name == "resume1.yaml" for f in result)
        assert any(f.name == "resume2.yml" for f in result)

    def test_returns_empty_list_for_nonexistent_dir(self) -> None:
        """Test returns empty list when directory doesn't exist."""
        nonexistent = Path("/nonexistent/directory")
        result = find_yaml_files(nonexistent)
        assert result == []

    def test_filters_by_pattern(self, tmp_path: Path) -> None:
        """Test filtering files by pattern."""
        (tmp_path / "john.yaml").write_text("config: {}")
        (tmp_path / "jane.yaml").write_text("config: {}")
        (tmp_path / "sample.yaml").write_text("config: {}")

        result = find_yaml_files(tmp_path, pattern="john")

        assert len(result) == 1
        assert result[0].name == "john.yaml"

    def test_sorts_results(self, tmp_path: Path) -> None:
        """Test results are sorted."""
        (tmp_path / "zebra.yaml").write_text("config: {}")
        (tmp_path / "apple.yaml").write_text("config: {}")
        (tmp_path / "middle.yaml").write_text("config: {}")

        result = find_yaml_files(tmp_path)

        names = [f.name for f in result]
        assert names == sorted(names)


class TestIterateYamlFiles:
    """Tests for iterate_yaml_files generator function."""

    def test_yields_yaml_files(self, tmp_path: Path) -> None:
        """Test yielding YAML files."""
        (tmp_path / "resume1.yaml").write_text("config: {}")
        (tmp_path / "resume2.yml").write_text("config: {}")

        result = list(iterate_yaml_files(tmp_path))

        assert len(result) == 2
        assert all(isinstance(f, Path) for f in result)

    def test_is_generator(self, tmp_path: Path) -> None:
        """Test that iterate_yaml_files returns a generator."""
        (tmp_path / "test.yaml").write_text("config: {}")

        result = iterate_yaml_files(tmp_path)

        # Verify it's a generator (has __next__)
        assert hasattr(result, "__next__")

    def test_yields_with_pattern(self, tmp_path: Path) -> None:
        """Test yielding files matching pattern."""
        (tmp_path / "john.yaml").write_text("config: {}")
        (tmp_path / "jane.yaml").write_text("config: {}")

        result = list(iterate_yaml_files(tmp_path, pattern="john"))

        assert len(result) == 1
        assert result[0].name == "john.yaml"


class TestGetResumeNameFromPath:
    """Tests for get_resume_name_from_path function."""

    def test_extracts_name_from_yaml_path(self) -> None:
        """Test extracting name from .yaml file."""
        path = Path("/some/dir/john_doe.yaml")
        result = get_resume_name_from_path(path)
        assert result == "john_doe"

    def test_extracts_name_from_yml_path(self) -> None:
        """Test extracting name from .yml file."""
        path = Path("/some/dir/jane_smith.yml")
        result = get_resume_name_from_path(path)
        assert result == "jane_smith"

    def test_extracts_name_with_special_characters(self) -> None:
        """Test extracting name with underscores and hyphens."""
        path = Path("/dir/resume-2024_final.yaml")
        result = get_resume_name_from_path(path)
        assert result == "resume-2024_final"

    def test_extracts_from_relative_path(self) -> None:
        """Test extracting name from relative path."""
        path = Path("input/sample.yaml")
        result = get_resume_name_from_path(path)
        assert result == "sample"
