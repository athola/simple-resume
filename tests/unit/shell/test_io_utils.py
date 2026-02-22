"""Tests for shell/io_utils.py - path and file handling utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.core.paths import Paths
from simple_resume.shell.io_utils import (
    candidate_yaml_path,
    ensure_directory_exists,
    find_resume_file,
    normalize_resume_name,
    read_yaml_file,
    resolve_output_path,
    resolve_paths_for_read,
)


class TestCandidateYamlPath:
    """Tests for candidate_yaml_path function."""

    def test_yaml_extension_returns_path(self) -> None:
        """Test that .yaml extension returns Path."""
        result = candidate_yaml_path("resume.yaml")
        assert result == Path("resume.yaml")

    def test_yml_extension_returns_path(self) -> None:
        """Test that .yml extension returns Path."""
        result = candidate_yaml_path("resume.yml")
        assert result == Path("resume.yml")

    def test_no_yaml_extension_returns_none(self) -> None:
        """Test that unsupported files return None."""
        result = candidate_yaml_path("resume.txt")
        assert result is None

    def test_json_without_path_returns_none(self) -> None:
        """Bare .json is treated as a resume name, not a direct path."""
        result = candidate_yaml_path("resume.json")
        assert result is None

    def test_json_with_path_returns_path(self) -> None:
        """.json is treated as a path when it includes directory components."""
        result = candidate_yaml_path("input/resume.json")
        assert result == Path("input/resume.json")


class TestResolvePathsForRead:
    """Tests for resolve_paths_for_read function."""

    def test_returns_supplied_paths_if_provided(self, tmp_path: Path) -> None:
        """Test returns supplied paths when provided."""
        paths = Paths(
            data=tmp_path,
            input=tmp_path / "input",
            output=tmp_path / "output",
            content=tmp_path / "content",
            templates=tmp_path / "templates",
            static=tmp_path / "static",
        )
        result = resolve_paths_for_read(paths, {}, None)
        assert result == paths

    def test_uses_overrides_when_no_supplied_paths(self, tmp_path: Path) -> None:
        """Test uses overrides when no supplied paths."""
        overrides = {"data_dir": tmp_path}
        result = resolve_paths_for_read(None, overrides, None)
        assert result.data == tmp_path

    def test_uses_candidate_parent_as_input(self, tmp_path: Path) -> None:
        """Test uses candidate parent directory as input."""
        candidate = tmp_path / "resumes" / "john.yaml"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("config: {}")

        result = resolve_paths_for_read(None, {}, candidate)
        assert result.input == candidate.parent

    def test_handles_candidate_in_input_subdirectory(self, tmp_path: Path) -> None:
        """Test special handling for candidate in 'input' subdirectory."""
        input_dir = tmp_path / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        candidate = input_dir / "john.yaml"
        candidate.write_text("config: {}")

        result = resolve_paths_for_read(None, {}, candidate)
        # When candidate is in "input" dir, base_dir should be parent.parent
        assert result.data == tmp_path

    @pytest.mark.parametrize("dirname", ["Input", "INPUT", "iNpUt"])
    def test_handles_candidate_in_case_variant_input_dir(
        self, tmp_path: Path, dirname: str
    ) -> None:
        """Case-insensitive matching of input/ directory name."""
        input_dir = tmp_path / dirname
        input_dir.mkdir(parents=True, exist_ok=True)
        candidate = input_dir / "john.yaml"
        candidate.write_text("config: {}")

        result = resolve_paths_for_read(None, {}, candidate)
        assert result.data == tmp_path

    def test_root_level_input_dir_raises(self) -> None:
        """Reject candidate in root-level input/ where grandparent is /."""
        candidate = Path("/input/resume.yaml")
        with pytest.raises(ValueError, match="root-level"):
            resolve_paths_for_read(None, {}, candidate)

    def test_fallback_with_no_inputs(self) -> None:
        """Test fallback behavior with no supplied paths or candidate."""
        result = resolve_paths_for_read(None, {}, None)
        assert isinstance(result, Paths)


class TestNormalizeResumeName:
    """Tests for normalize_resume_name function."""

    def test_strips_yaml_extension(self) -> None:
        """Test stripping .yaml extension."""
        result = normalize_resume_name("john_doe.yaml")
        assert result == "john_doe"

    def test_strips_yml_extension(self) -> None:
        """Test stripping .yml extension."""
        result = normalize_resume_name("jane_doe.yml")
        assert result == "jane_doe"

    def test_strips_json_extension(self) -> None:
        """Test stripping .json extension."""
        result = normalize_resume_name("john_doe.json")
        assert result == "john_doe"

    def test_handles_empty_string(self) -> None:
        """Test handling empty string returns default."""
        result = normalize_resume_name("")
        assert result == "sample_1"  # FILE_DEFAULT from shell.config

    def test_handles_pathlike_without_extension(self) -> None:
        """Test handling PathLike without extension."""
        result = normalize_resume_name(Path("john_doe"))
        assert result == "john_doe"

    def test_handles_path_object(self) -> None:
        """Test handling Path object with extension."""
        result = normalize_resume_name(Path("data/john.yaml"))
        assert result == "john"

    def test_handles_non_string_input(self) -> None:
        """Test handling non-string/non-path input (runtime type check bypass)."""
        # Type hint says str | PathLike but runtime can receive other types
        result = normalize_resume_name(12345)  # type: ignore[arg-type]
        assert result == "12345"


class TestFindResumeFile:
    """Tests for find_resume_file function."""

    def test_finds_yaml_file(self, tmp_path: Path) -> None:
        """Test finding .yaml file."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        resume_file = input_dir / "john.yaml"
        resume_file.write_text("config: {}")

        result = find_resume_file("john", input_dir)
        assert result == resume_file

    def test_finds_yml_file(self, tmp_path: Path) -> None:
        """Test finding .yml file."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        resume_file = input_dir / "jane.yml"
        resume_file.write_text("config: {}")

        result = find_resume_file("jane", input_dir)
        assert result == resume_file

    def test_finds_json_file(self, tmp_path: Path) -> None:
        """Test finding .json file."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        resume_file = input_dir / "jane.json"
        resume_file.write_text("{}")

        result = find_resume_file("jane", input_dir)
        assert result == resume_file

    def test_returns_fallback_path_when_not_found(self, tmp_path: Path) -> None:
        """Test returns fallback path when file not found."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        result = find_resume_file("missing", input_dir)
        assert result == input_dir / "missing.yaml"


class TestReadYamlFile:
    """Tests for read_yaml_file function."""

    def test_reads_valid_yaml_file(self, tmp_path: Path) -> None:
        """Test reading valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("name: John\nage: 30")

        result = read_yaml_file(yaml_file)
        assert result == {"name": "John", "age": 30}

    def test_handles_empty_yaml_file(self, tmp_path: Path) -> None:
        """Test handling empty YAML file returns empty dict."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = read_yaml_file(yaml_file)
        assert result == {}

    def test_raises_on_non_dict_yaml(self, tmp_path: Path) -> None:
        """Test raises ValueError for non-dict YAML content."""
        yaml_file = tmp_path / "list.yaml"
        yaml_file.write_text("- item1\n- item2")

        with pytest.raises(ValueError, match="must contain a dictionary"):
            read_yaml_file(yaml_file)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Test raises FileNotFoundError for missing file."""
        yaml_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError, match="YAML file not found"):
            read_yaml_file(yaml_file)


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test creating directory."""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_directory_exists(new_dir)
        assert new_dir.exists()
        assert result == new_dir

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Test creating nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        result = ensure_directory_exists(nested_dir)
        assert nested_dir.exists()
        assert result == nested_dir


class TestResolveOutputPath:
    """Tests for resolve_output_path function."""

    def test_adds_extension_if_missing(self, tmp_path: Path) -> None:
        """Test adds extension if missing."""
        result = resolve_output_path(tmp_path, "output", ".pdf")
        assert result == tmp_path / "output.pdf"

    def test_does_not_duplicate_extension(self, tmp_path: Path) -> None:
        """Test does not duplicate extension."""
        result = resolve_output_path(tmp_path, "output.pdf", ".pdf")
        assert result == tmp_path / "output.pdf"

    def test_creates_base_directory(self, tmp_path: Path) -> None:
        """Test creates base directory if it doesn't exist."""
        base_dir = tmp_path / "output"
        assert not base_dir.exists()

        result = resolve_output_path(base_dir, "file", ".html")
        assert base_dir.exists()
        assert result == base_dir / "file.html"
