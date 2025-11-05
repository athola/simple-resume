from __future__ import annotations

import os
from pathlib import Path

import pytest

from simple_resume import validation
from simple_resume.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)
from simple_resume.validation import (
    validate_directory_path,
    validate_file_path,
    validate_format,
    validate_output_path,
    validate_resume_data,
    validate_template_name,
    validate_yaml_file,
)


def test_validate_format_accepts_supported(story) -> None:
    story.given("a supported format string with extra whitespace")
    normalized = validate_format("  PDF ")

    story.then("the value is normalized to lowercase")
    assert normalized == "pdf"


def test_validate_format_rejects_unknown(story) -> None:
    story.given("an unsupported format string")
    with pytest.raises(ValidationError, match="Unsupported"):
        validate_format("docx")


def test_validate_format_empty_input(story) -> None:
    story.given("an empty format string")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_format("")


def test_validate_file_path_with_existing_file(story, tmp_path: Path) -> None:
    story.given("a file that exists on disk")
    file_path = tmp_path / "resume.txt"
    file_path.write_text("example")

    validated = validate_file_path(file_path, must_exist=True)

    story.then("the validated path matches the real file")
    assert validated == file_path.resolve()


def test_validate_file_path_rejects_missing_file(story, tmp_path: Path) -> None:
    story.given("a path to a non-existent file")
    missing = tmp_path / "missing.yaml"

    with pytest.raises(FileSystemError, match="does not exist"):
        validate_file_path(missing)


def test_validate_file_path_empty_string(story) -> None:
    story.given("an empty string path")
    with pytest.raises(FileSystemError, match="cannot be empty"):
        validate_file_path("")


def test_validate_file_path_resolves_relative_path(story, tmp_path: Path) -> None:
    story.given("a relative path provided as a string")
    cwd = tmp_path / "work"
    cwd.mkdir()
    file_path = cwd / "resume.txt"
    file_path.write_text("content")

    old_cwd = os.getcwd()
    os.chdir(cwd)
    try:
        validated = validate_file_path("resume.txt")
    finally:
        os.chdir(old_cwd)

    story.then("the path is resolved to an absolute location")
    assert validated == file_path.resolve()


def test_validate_file_path_enforces_extension(story, tmp_path: Path) -> None:
    story.given("a temporary file that does not use YAML extension")
    file_path = tmp_path / "data.txt"
    file_path.write_text("content")

    with pytest.raises(FileSystemError, match="Invalid file extension"):
        validate_file_path(file_path, allowed_extensions=(".yaml", ".yml"))


def test_validate_file_path_rejects_large_files(
    story,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    story.given("a file that exceeds the configured size limit")
    file_path = tmp_path / "large.dat"
    file_path.write_bytes(b"x" * 2048)  # 2KB

    monkeypatch.setattr(validation, "MAX_FILE_SIZE_MB", 0.001)

    with pytest.raises(FileSystemError, match="File too large"):
        validate_file_path(file_path)


def test_validate_directory_path_creates_when_allowed(
    story,
    tmp_path: Path,
) -> None:
    story.given("a directory path that does not yet exist")
    target_dir = tmp_path / "new-dir"

    validated = validate_directory_path(target_dir, create_if_missing=True)

    story.then("the directory is created and returned")
    assert validated == target_dir.resolve()
    assert target_dir.exists() and target_dir.is_dir()


def test_validate_directory_path_rejects_file(story, tmp_path: Path) -> None:
    story.given("a path that points to an existing file")
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    with pytest.raises(FileSystemError, match="not a directory"):
        validate_directory_path(file_path)


def test_validate_directory_path_requires_existing_when_flagged(
    story, tmp_path: Path
) -> None:
    story.given("a missing directory with must_exist enabled")
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileSystemError, match="does not exist"):
        validate_directory_path(missing_dir, must_exist=True)


def test_validate_directory_path_reports_creation_failure(
    story,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    story.given("mkdir raises an OSError during directory creation")
    target_dir = tmp_path / "blocked"

    def fake_mkdir(self, parents=True, exist_ok=True):
        raise PermissionError("denied")

    monkeypatch.setattr(validation.Path, "mkdir", fake_mkdir, raising=False)

    with pytest.raises(FileSystemError, match="Failed to create directory"):
        validate_directory_path(target_dir, create_if_missing=True)


def test_validate_template_name_accepts_simple_patterns(story) -> None:
    story.given("a template name containing hyphens and underscores")
    name = validate_template_name(" business-template_2025 ")

    story.then("the cleaned template name is returned")
    assert name == "business-template_2025"


def test_validate_template_name_rejects_illegal_characters(story) -> None:
    story.given("a template name with disallowed punctuation")
    with pytest.raises(ConfigurationError, match="Invalid template name"):
        validate_template_name("bad/template")


def test_validate_template_name_empty(story) -> None:
    story.given("an empty template name")
    with pytest.raises(ConfigurationError, match="cannot be empty"):
        validate_template_name("")


def test_validate_yaml_file_requires_yaml_extension(story, tmp_path: Path) -> None:
    story.given("a YAML file stored under the data directory")
    yaml_path = tmp_path / "resume.yaml"
    yaml_path.write_text("full_name: Example")

    validated = validate_yaml_file(yaml_path)

    story.then("the YAML path is accepted")
    assert validated == yaml_path.resolve()


def test_validate_yaml_file_rejects_wrong_extension(story, tmp_path: Path) -> None:
    story.given("a JSON file where YAML is expected")
    json_path = tmp_path / "resume.json"
    json_path.write_text("{}")

    with pytest.raises(FileSystemError, match="Invalid file extension"):
        validate_yaml_file(json_path)


def test_validate_resume_data_checks_full_name(story) -> None:
    story.given("resume data without a full name")
    with pytest.raises(ValidationError, match="must include 'full_name'"):
        validate_resume_data({"config": {}})


def test_validate_resume_data_requires_dictionary(story) -> None:
    story.given("resume data that is not a dictionary")
    with pytest.raises(ValidationError, match="must be a dictionary"):
        validate_resume_data(["not-a-dict"])  # type: ignore[arg-type]


def test_validate_resume_data_empty_dictionary(story) -> None:
    story.given("resume data that is an empty dictionary")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_resume_data({})


def test_validate_resume_data_requires_non_empty_full_name(story) -> None:
    story.given("resume data with an empty full_name string")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_resume_data({"full_name": ""})


def test_validate_resume_data_config_must_be_dict(story) -> None:
    story.given("resume data whose config entry is not a dictionary")
    with pytest.raises(ValidationError, match="must be a dictionary"):
        validate_resume_data({"full_name": "User", "config": "not-a-dict"})


def test_validate_output_path_accepts_matching_extension(
    story,
    tmp_path: Path,
) -> None:
    story.given("an output path with the correct extension")
    output_path = tmp_path / "result.pdf"

    validated = validate_output_path(output_path, "pdf")

    story.then("the path is returned without modification")
    assert validated == output_path


def test_validate_output_path_rejects_mismatch(story, tmp_path: Path) -> None:
    story.given("an output path whose suffix does not match the requested format")
    output_path = tmp_path / "result.html"

    with pytest.raises(FileSystemError, match="doesn't match format"):
        validate_output_path(output_path, "pdf")
