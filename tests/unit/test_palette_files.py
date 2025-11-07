"""Tests for standalone palette file functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from simple_resume.core.resume import Resume
from simple_resume.exceptions import ConfigurationError
from simple_resume.utilities import (
    apply_external_palette,
    load_palette_from_file,
)


def test_load_palette_from_file_with_palette_block(story) -> None:
    story.given("a palette YAML file containing a nested palette block")
    palette_content = """
palette:
  source: generator
  type: hcl
  size: 5
  seed: 42
  hue_range: [200, 220]
  luminance_range: [0.25, 0.7]
  chroma: 0.25
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("load_palette_from_file parses the document")
        result = load_palette_from_file(temp_path)

        story.then("the palette metadata is returned verbatim")
        assert result["palette"]["source"] == "generator"
        assert result["palette"]["type"] == "hcl"
        assert result["palette"]["size"] == 5
        assert result["palette"]["seed"] == 42
        assert result["palette"]["hue_range"] == [200, 220]
        assert result["palette"]["luminance_range"] == [0.25, 0.7]
        assert result["palette"]["chroma"] == 0.25
    finally:
        temp_path.unlink()


def test_load_palette_from_file_without_palette_block(story) -> None:
    story.given("a palette YAML file with top-level color metadata")
    palette_content = """
source: registry
name: test_palette
colors:
  - "#FF0000"
  - "#00FF00"
  - "#0000FF"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("load_palette_from_file coerces the structure into palette block")
        result = load_palette_from_file(temp_path)

        story.then("the return value exposes the expected registry metadata")
        assert result["palette"]["source"] == "registry"
        assert result["palette"]["name"] == "test_palette"
        assert result["palette"]["colors"] == ["#FF0000", "#00FF00", "#0000FF"]
    finally:
        temp_path.unlink()


def test_load_palette_from_file_not_found(story) -> None:
    story.given("a path to a non-existent palette file")
    story.then("loading the palette raises FileNotFoundError")
    with pytest.raises(FileNotFoundError, match="Palette file not found"):
        load_palette_from_file("nonexistent_palette.yaml")


def test_load_palette_from_file_invalid_extension(story) -> None:
    story.given("a palette file with .txt extension")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("palette:\n  source: generator")
        temp_path = Path(f.name)

    try:
        story.then("load_palette_from_file rejects non-YAML files")
        with pytest.raises(ValueError, match="Palette file must be a YAML file"):
            load_palette_from_file(temp_path)
    finally:
        temp_path.unlink()


def test_load_palette_from_file_invalid_yaml(story) -> None:
    story.given("a palette file with malformed YAML syntax")
    invalid_yaml = """
palette:
  source: generator
  size: [unclosed bracket
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(invalid_yaml)
        temp_path = Path(f.name)

    try:
        story.then("PyYAML parsing errors propagate to the caller")
        with pytest.raises(yaml.YAMLError):
            load_palette_from_file(temp_path)
    finally:
        temp_path.unlink()


def test_load_palette_from_file_non_dict_content(story) -> None:
    story.given("a palette file whose root node is a list")
    invalid_content = """
- item1
- item2
- item3
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(invalid_content)
        temp_path = Path(f.name)

    try:
        story.then("a ValueError explains the expected dictionary format")
        with pytest.raises(
            ValueError,
            match="YAML file must contain a dictionary at the root level",
        ):
            load_palette_from_file(temp_path)
    finally:
        temp_path.unlink()


def test_apply_external_palette(story) -> None:
    story.given("a resume config and palette YAML to merge")
    base_config = {
        "template": "resume_base",
        "full_name": "John Doe",
        "job_title": "Software Engineer",
    }

    palette_content = """
palette:
  source: generator
  type: hcl
  size: 5
  seed: 123
  hue_range: [10, 30]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("apply_external_palette merges the palette metadata")
        result = apply_external_palette(base_config, temp_path)

        story.then("the merged config includes palette info without mutating input")
        assert result["template"] == "resume_base"
        assert result["full_name"] == "John Doe"
        assert result["job_title"] == "Software Engineer"
        assert result["palette"]["source"] == "generator"
        assert result["palette"]["hue_range"] == [10, 30]
        assert "palette" not in base_config
    finally:
        temp_path.unlink()


def test_apply_external_palette_overrides_existing(story) -> None:
    story.given("a config that already specifies a palette")
    base_config = {
        "template": "resume_base",
        "palette": {"source": "registry", "name": "old_palette"},
    }

    palette_content = """
palette:
  source: generator
  type: hcl
  size: 5
  seed: 456
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("apply_external_palette loads the replacement file")
        result = apply_external_palette(base_config, temp_path)

        story.then("the original palette fields are replaced by the file contents")
        assert result["palette"]["source"] == "generator"
        assert result["palette"]["type"] == "hcl"
        assert result["palette"]["size"] == 5
        assert result["palette"]["seed"] == 456
        assert "name" not in result["palette"]
    finally:
        temp_path.unlink()


def test_resume_with_config_palette_file(story) -> None:
    story.given("a Resume instance without palette data and a palette file")
    # Create a mock resume data
    resume_data = {
        "template": "resume_base",
        "full_name": "Test User",
        "config": {"theme_color": "#0395DE"},
    }

    palette_content = """
palette:
  source: generator
  type: hcl
  size: 5
  seed: 789
  hue_range: [200, 250]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        resume = Resume.from_data(resume_data, name="test")
        story.when("with_config is called using the palette file path")
        updated_resume = resume.with_config(palette_file=str(temp_path))

        story.then("palette metadata merges without clobbering other config")
        assert "palette" in updated_resume._data["config"]
        assert updated_resume._data["config"]["palette"]["hue_range"] == [200, 250]
        assert updated_resume._data["config"]["theme_color"] == "#0395DE"
    finally:
        temp_path.unlink()


def test_resume_with_config_invalid_palette_file(story) -> None:
    story.given("a Resume instance and a missing palette file path")
    resume_data = {"template": "resume_base", "full_name": "Test User"}

    resume = Resume.from_data(resume_data, name="test")

    story.then("with_config raises ConfigurationError when file is missing")
    with pytest.raises(ConfigurationError, match="Failed to load palette file"):
        resume.with_config(palette_file="nonexistent_palette.yaml")


def test_resume_with_config_preserves_other_overrides(story) -> None:
    story.given("a palette file plus additional config overrides")
    resume_data = {"template": "resume_base", "full_name": "Test User"}

    palette_content = """
palette:
  source: generator
  type: hcl
  size: 5
  seed: 999
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        resume = Resume.from_data(resume_data, name="test")
        story.when("with_config applies both palette file and explicit overrides")
        updated_resume = resume.with_config(
            palette_file=str(temp_path), theme_color="#FF0000", page_width=220
        )

        story.then("palette data merges while manual overrides persist")
        assert updated_resume._data["config"]["palette"]["source"] == "generator"
        assert updated_resume._data["config"]["theme_color"] == "#FF0000"
        assert updated_resume._data["config"]["page_width"] == 220
    finally:
        temp_path.unlink()


def test_load_palette_from_file_with_direct_colors(story) -> None:
    """Regression coverage for palette files with direct color definitions."""
    story.given("a palette file with direct color values under palette key")
    palette_content = """
palette:
  theme_color: "#D04040"
  sidebar_color: "#E8B8C0"
  bar_background_color: "#CCCCCC"
  date2_color: "#666666"
  sidebar_text_color: "#333333"
  frame_color: "#C04040"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("load_palette_from_file parses the document")
        result = load_palette_from_file(temp_path)

        story.then("direct color entries are returned without registry metadata")
        assert result["palette"]["theme_color"] == "#D04040"
        assert result["palette"]["sidebar_color"] == "#E8B8C0"
        assert result["palette"]["bar_background_color"] == "#CCCCCC"
        assert result["palette"]["date2_color"] == "#666666"
        assert result["palette"]["sidebar_text_color"] == "#333333"
        assert result["palette"]["frame_color"] == "#C04040"
        assert "source" not in result["palette"]
        assert "name" not in result["palette"]
    finally:
        temp_path.unlink()


def test_load_palette_file_with_nested_config_block(story) -> None:
    """Palette files wrapped in a config block should be supported."""
    story.given("a palette file that keeps colors under a config block")
    palette_content = """
config:
  theme_color: "#123456"
  sidebar_color: "#FAFAFA"
  text_color: "#222222"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        story.when("load_palette_from_file parses the nested config payload")
        result = load_palette_from_file(temp_path)

        story.then("the nested config values are returned as palette data")
        assert result["palette"]["theme_color"] == "#123456"
        assert result["palette"]["sidebar_color"] == "#FAFAFA"
        assert result["palette"]["text_color"] == "#222222"
    finally:
        temp_path.unlink()


def test_resume_with_direct_color_palette_validates_successfully(story) -> None:
    """Ensure direct color palette files validate without errors."""
    story.given("a resume that loads a palette file containing direct colors")
    resume_data = {
        "template": "resume_base",
        "full_name": "Test User",
        "config": {},
    }

    palette_content = """
palette:
  theme_color: "#D04040"
  sidebar_color: "#E8B8C0"
  bar_background_color: "#CCCCCC"
  date2_color: "#666666"
  frame_color: "#C04040"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(palette_content)
        temp_path = Path(f.name)

    try:
        resume = Resume.from_data(resume_data, name="test")
        updated_resume = resume.with_config(palette_file=str(temp_path))

        story.when("the updated resume validates")
        validation_result = updated_resume.validate()

        story.then("validation succeeds and palette colors are present")
        assert validation_result.is_valid, (
            f"Validation failed: {validation_result.errors}"
        )
        config = updated_resume._data["config"]
        assert config["palette"]["theme_color"] == "#D04040"
        assert config["palette"]["sidebar_color"] == "#E8B8C0"
        assert config["palette"]["bar_background_color"] == "#CCCCCC"
    finally:
        temp_path.unlink()
