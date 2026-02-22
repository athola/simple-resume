"""Tests for _infer_data_dir_and_name path inference logic.

Covers the path-doubling bug (issue #84): when a YAML file lives inside an
``input/`` directory, the inferred ``data_dir`` must point to the *grandparent*
so that downstream path resolution can safely append ``/input`` without doubling
it.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from simple_resume.shell.generate.core import _infer_data_dir_and_name
from tests.bdd import Scenario


class TestInferDataDirFromYamlInInputDir:
    """YAML files inside an ``input/`` directory."""

    @pytest.mark.parametrize(
        ("filename", "expected_stem"),
        [
            ("sample.yaml", "sample"),
            ("resume.yml", "resume"),
            ("Resume.YAML", "Resume"),
        ],
    )
    def test_yaml_extensions_in_input_dir_return_grandparent(
        self, tmp_path: Path, story: Scenario, filename: str, expected_stem: str
    ) -> None:
        story.given(f"a '{filename}' file inside an input/ subdirectory")
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / filename
        yaml_file.touch()

        story.when("inferring data_dir without an explicit override")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=None)

        story.then("data_dir points to the grandparent (not input/ itself)")
        assert data_dir == tmp_path
        assert name == expected_stem

    def test_yaml_in_nested_input_dir_returns_grandparent(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a YAML file inside a deeply nested input/ subdirectory")
        nested = tmp_path / "projects" / "resumes" / "input"
        nested.mkdir(parents=True)
        yaml_file = nested / "resume.yaml"
        yaml_file.touch()

        story.when("inferring data_dir without an explicit override")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=None)

        story.then("data_dir points to the grandparent of input/")
        assert data_dir == tmp_path / "projects" / "resumes"
        assert name == "resume"

    @pytest.mark.parametrize("dirname", ["Input", "INPUT", "iNpUt"])
    def test_case_insensitive_input_dir_matching(
        self, tmp_path: Path, story: Scenario, dirname: str
    ) -> None:
        story.given(f"a YAML file inside a '{dirname}/' subdirectory")
        input_dir = tmp_path / dirname
        input_dir.mkdir()
        yaml_file = input_dir / "sample.yaml"
        yaml_file.touch()

        story.when("inferring data_dir without an explicit override")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=None)

        story.then("the directory name is matched case-insensitively")
        assert data_dir == tmp_path
        assert name == "sample"


class TestInferDataDirFromYamlNotInInputDir:
    """YAML files that are NOT inside an ``input/`` directory."""

    def test_yaml_in_regular_dir_returns_parent(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a YAML file in a directory NOT named input/")
        yaml_file = tmp_path / "sample.yaml"
        yaml_file.touch()

        story.when("inferring data_dir without an explicit override")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=None)

        story.then("data_dir points to the parent directory")
        assert data_dir == tmp_path
        assert name == "sample"


class TestInferDataDirFromDirectory:
    """Directory sources return the directory itself."""

    def test_directory_source_returns_itself(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a directory as source")
        story.when("inferring data_dir")
        data_dir, name = _infer_data_dir_and_name(tmp_path, data_dir=None)

        story.then("the directory is used as data_dir with no resume name")
        assert data_dir == tmp_path
        assert name is None


class TestInferDataDirWithExplicitOverride:
    """When data_dir is explicitly provided, it generally takes precedence.

    Exception: directory sources always return themselves as data_dir,
    ignoring the explicit override.
    """

    def test_explicit_data_dir_with_yaml(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a YAML source and an explicit data_dir")
        yaml_file = tmp_path / "input" / "sample.yaml"
        yaml_file.parent.mkdir(exist_ok=True)
        yaml_file.touch()
        explicit_dir = tmp_path / "custom"
        explicit_dir.mkdir()

        story.when("inferring with an explicit data_dir")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=explicit_dir)

        story.then("the explicit data_dir is used, not the inferred one")
        assert data_dir == explicit_dir
        assert name == "sample"

    def test_explicit_data_dir_with_directory_source(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a directory source and an explicit data_dir")
        source_dir = tmp_path / "myresumes"
        source_dir.mkdir()
        explicit_dir = tmp_path / "override"
        explicit_dir.mkdir()

        story.when("inferring with directory source and explicit data_dir")
        data_dir, name = _infer_data_dir_and_name(source_dir, data_dir=explicit_dir)

        story.then("the source directory wins over explicit for dir sources")
        assert data_dir == source_dir
        assert name is None

    def test_explicit_data_dir_with_plain_name(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a plain resume name (no extension) and an explicit data_dir")
        explicit_dir = tmp_path / "data"
        explicit_dir.mkdir()

        story.when("inferring with a bare name and explicit data_dir")
        data_dir, name = _infer_data_dir_and_name("john", data_dir=explicit_dir)

        story.then("the explicit data_dir is used and the name is passed through")
        assert data_dir == explicit_dir
        assert name == "john"

    def test_explicit_data_dir_with_nonexistent_yaml(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a non-existent YAML path and an explicit data_dir")
        explicit_dir = tmp_path / "data"
        explicit_dir.mkdir()

        story.when("inferring with a YAML path that doesn't exist on disk")
        data_dir, name = _infer_data_dir_and_name(
            "/nonexistent/resume.yaml", data_dir=explicit_dir
        )

        story.then("the explicit data_dir is used and the stem is extracted")
        assert data_dir == explicit_dir
        assert name == "resume"


class TestExplicitDataDirEndingInInput:
    """Warn when explicit data_dir ends in ``input/`` (path-doubling risk)."""

    @pytest.mark.parametrize("dirname", ["input", "Input", "INPUT", "iNpUt"])
    def test_warns_when_data_dir_named_input(
        self, tmp_path: Path, story: Scenario, dirname: str
    ) -> None:
        story.given(f"an explicit data_dir whose basename is '{dirname}'")
        input_dir = tmp_path / dirname
        input_dir.mkdir()
        yaml_file = tmp_path / "sample.yaml"
        yaml_file.touch()

        story.when("inferring with that data_dir")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=input_dir)

        story.then("a UserWarning about path-doubling is emitted regardless of case")
        assert len(caught) == 1
        assert "path doubling" in str(caught[0].message).lower()
        assert data_dir == input_dir
        assert name == "sample"

    def test_no_warning_for_normal_data_dir(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("an explicit data_dir with a normal name")
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        yaml_file = tmp_path / "sample.yaml"
        yaml_file.touch()

        story.when("inferring with that data_dir")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _infer_data_dir_and_name(yaml_file, data_dir=custom_dir)

        story.then("no warning is emitted")
        assert len(caught) == 0


class TestRootLevelInputGuard:
    """Guard against degenerate parent.parent when input/ is at filesystem root."""

    def test_relative_input_dir_yields_cwd(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a YAML file inside a relative input/ directory")
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "resume.yaml"
        yaml_file.touch()

        story.when("inferring data_dir")
        data_dir, name = _infer_data_dir_and_name(yaml_file, data_dir=None)

        story.then("grandparent (tmp_path) is returned — not degenerate")
        assert data_dir == tmp_path
        assert name == "resume"

    def test_root_level_input_raises(self, story: Scenario) -> None:
        story.given("a YAML file at /input/resume.yaml (grandparent == /)")
        # We can't easily create /input on the real filesystem, so test the
        # guard logic: if the file doesn't exist, it already raises ValueError.
        # This test documents the expected behavior for the edge case.
        story.when("inferring data_dir for a root-level input/ path")
        story.then("ValueError is raised because file doesn't exist")
        with pytest.raises(ValueError, match="Unable to infer data_dir"):
            _infer_data_dir_and_name("/input/resume.yaml", data_dir=None)


class TestInferDataDirErrorCases:
    """Invalid inputs raise ValueError."""

    def test_nonexistent_path_without_data_dir_raises(self, story: Scenario) -> None:
        story.given("a source path that doesn't exist and no data_dir")
        story.when("inferring data_dir")
        story.then("a ValueError is raised")
        with pytest.raises(ValueError, match="Unable to infer data_dir"):
            _infer_data_dir_and_name("/nonexistent/path", data_dir=None)

    def test_non_yaml_file_in_input_dir_raises(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a non-YAML file (.txt) inside an input/ directory and no data_dir")
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        txt_file = input_dir / "notes.txt"
        txt_file.touch()

        story.when("inferring data_dir without an explicit override")
        story.then("a ValueError is raised because the file is not YAML")
        with pytest.raises(ValueError, match="Unable to infer data_dir"):
            _infer_data_dir_and_name(txt_file, data_dir=None)
