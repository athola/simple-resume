"""Input validation utilities for Simple-Resume.

This module provides validation functions for user inputs, file paths,
and configuration values to ensure data integrity and provide helpful
error messages.
"""

from pathlib import Path
from typing import Any

from .constants import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_FORMATS,
    YAML_EXTENSIONS,
    OutputFormat,
)
from .exceptions import ConfigurationError, FileSystemError, ValidationError


def validate_format(format_str: str, param_name: str = "format") -> str:
    """Validate and normalize format string.

    Args:
        format_str: Format string to validate (pdf, html, latex)
        param_name: Parameter name for error messages

    Returns:
        Normalized format string (lowercase)

    Raises:
        ValidationError: If format is not supported

    """
    if not format_str:
        raise ValidationError(f"{param_name} cannot be empty")

    normalized = format_str.lower().strip()

    if not OutputFormat.is_valid(normalized):
        raise ValidationError(
            f"Unsupported {param_name}: '{format_str}'. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    return normalized


def validate_file_path(
    file_path: str | Path,
    *,
    must_exist: bool = True,
    must_be_file: bool = True,
    allowed_extensions: tuple[str, ...] | None = None,
) -> Path:
    """Validate file path.

    Args:
        file_path: Path to validate
        must_exist: If True, path must exist
        must_be_file: If True, path must be a file (not directory)
        allowed_extensions: If provided, file must have one of these extensions

    Returns:
        Validated Path object

    Raises:
        FileSystemError: If path validation fails




    """
    if not file_path:
        raise FileSystemError("File path cannot be empty")

    path = Path(file_path) if isinstance(file_path, str) else file_path

    # Check if absolute path or resolve to absolute
    if not path.is_absolute():
        path = path.resolve()

    if must_exist and not path.exists():
        raise FileSystemError(f"Path does not exist: {path}")

    if must_be_file and must_exist and not path.is_file():
        raise FileSystemError(f"Path is not a file: {path}")

    if allowed_extensions and path.suffix.lower() not in allowed_extensions:
        raise FileSystemError(
            f"Invalid file extension '{path.suffix}'. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    # Check file size if it exists
    if must_exist and path.is_file():
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise FileSystemError(
                f"File too large: {size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"
            )

    return path


def validate_directory_path(
    dir_path: str | Path, *, must_exist: bool = False, create_if_missing: bool = False
) -> Path:
    """Validate directory path.

    Args:
        dir_path: Directory path to validate
        must_exist: If True, directory must exist
        create_if_missing: If True, create directory if it doesn't exist

    Returns:
        Validated Path object

    Raises:
        FileSystemError: If path validation fails

    """
    if not dir_path:
        raise FileSystemError("Directory path cannot be empty")

    path = Path(dir_path) if isinstance(dir_path, str) else dir_path

    if not path.is_absolute():
        path = path.resolve()

    if must_exist and not path.exists():
        raise FileSystemError(f"Directory does not exist: {path}")

    if path.exists() and not path.is_dir():
        raise FileSystemError(f"Path is not a directory: {path}")

    if create_if_missing and not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise FileSystemError(f"Failed to create directory {path}: {e}") from e

    return path


def validate_template_name(template: str) -> str:
    """Validate template name.

    Args:
        template: Template name to validate

    Returns:
        Validated template name

    Raises:
        ConfigurationError: If template is invalid

    """
    if not template:
        raise ConfigurationError("Template name cannot be empty")

    template = template.strip()

    # Allow custom templates (don't enforce SUPPORTED_TEMPLATES strictly)
    # Just ensure it's a reasonable string
    if not template.replace("_", "").replace("-", "").isalnum():
        message = (
            f"Invalid template name: '{template}'. "
            "Template names should contain only alphanumeric characters, "
            "hyphens, and underscores."
        )
        raise ConfigurationError(message)

    return template


def validate_yaml_file(file_path: str | Path) -> Path:
    """Validate YAML resume file.

    Args:
        file_path: Path to YAML file

    Returns:
        Validated Path object

    Raises:
        FileSystemError: If file validation fails


    """
    return validate_file_path(
        file_path,
        must_exist=True,
        must_be_file=True,
        allowed_extensions=YAML_EXTENSIONS,
    )


def validate_resume_data(data: dict[str, Any]) -> None:
    """Validate basic resume data structure.

    Args:
        data: Resume data dictionary

    Raises:
        ValidationError: If data structure is invalid

    """
    if not isinstance(data, dict):
        raise ValidationError("Resume data must be a dictionary")

    if not data:
        raise ValidationError("Resume data cannot be empty")

    # Check for required fields
    if "full_name" not in data:
        raise ValidationError("Resume data must include 'full_name'")

    if not data.get("full_name"):
        raise ValidationError("'full_name' cannot be empty")

    # Check config if present
    if "config" in data:
        if not isinstance(data["config"], dict):
            raise ValidationError("'config' must be a dictionary")


def validate_output_path(output_path: str | Path, format_type: str) -> Path:
    """Validate output file path for generated resume.

    Args:
        output_path: Output file path
        format_type: Format type (pdf, html)

    Returns:
        Validated Path object

    Raises:
        FileSystemError: If path validation fails

    """
    path = Path(output_path) if isinstance(output_path, str) else output_path

    # Validate parent directory
    if path.parent and path.parent != Path("."):
        validate_directory_path(path.parent, must_exist=False, create_if_missing=False)

    # Check file extension matches format
    expected_ext = f".{format_type.lower()}"
    if path.suffix.lower() != expected_ext:
        message = (
            f"Output path extension '{path.suffix}' doesn't match format "
            f"'{format_type}'. Expected: {expected_ext}"
        )
        raise FileSystemError(message)

    return path
