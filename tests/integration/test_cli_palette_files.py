"""Integration tests for CLI palette file functionality."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from simple_resume.cli import _build_config_overrides


def test_build_config_overrides_with_palette_file(story, tmp_path: Path) -> None:
    story.given("the CLI receives an absolute palette file path")
    palette_file = tmp_path / "palette.yaml"
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides processes the namespace")
    overrides = _build_config_overrides(args)

    story.then("the palette_file override is populated and color_scheme omitted")
    assert overrides["palette_file"] == str(palette_file)
    assert "color_scheme" not in overrides


def test_build_config_overrides_with_relative_path(
    story, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    story.given("the palette flag references a relative YAML path")
    monkeypatch.chdir(tmp_path)
    palette_dir = Path("palettes")
    palette_dir.mkdir()
    palette_file = palette_dir / "blue-theme.yaml"
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides is evaluated")
    overrides = _build_config_overrides(args)

    story.then("palette_file preserves the relative path and no color_scheme is set")
    assert overrides["palette_file"] == str(palette_file)
    assert "color_scheme" not in overrides


def test_build_config_overrides_with_yaml_extension(story, tmp_path: Path) -> None:
    story.given("the palette flag ends with .yaml")
    palette_file = tmp_path / "theme.yaml"
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides parses arguments")
    overrides = _build_config_overrides(args)

    story.then("the YAML file is treated as palette_file")
    assert overrides["palette_file"] == str(palette_file)
    assert "color_scheme" not in overrides


def test_build_config_overrides_with_yml_extension(story, tmp_path: Path) -> None:
    story.given("the palette flag ends with .yml")
    palette_file = tmp_path / "theme.yml"
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides runs")
    overrides = _build_config_overrides(args)

    story.then("the .yml file is also mapped to palette_file")
    assert overrides["palette_file"] == str(palette_file)
    assert "color_scheme" not in overrides


def test_build_config_overrides_with_palette_name(story) -> None:
    story.given("the palette flag is a registry name without .yaml suffix")
    args = Namespace(
        palette="ocean_blue",
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides executes")
    overrides = _build_config_overrides(args)

    story.then("color_scheme is set and palette_file omitted")
    assert overrides["color_scheme"] == "ocean_blue"
    assert "palette_file" not in overrides


def test_build_config_overrides_with_windows_path(story, tmp_path: Path) -> None:
    story.given("the palette path uses OS-specific separators")
    palette_file = tmp_path / "palettes" / "theme.yaml"
    palette_file.parent.mkdir(parents=True)
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides inspects the path")
    overrides = _build_config_overrides(args)

    story.then("palette_file preserves the Windows path verbatim")
    assert overrides["palette_file"] == str(palette_file)
    assert "color_scheme" not in overrides


def test_build_config_overrides_with_other_config_overrides(
    story, tmp_path: Path
) -> None:
    story.given("palette file flag plus theme and page size overrides")
    palette_file = tmp_path / "palettes" / "theme.yaml"
    palette_file.parent.mkdir(parents=True)
    palette_file.write_text("palette: {}", encoding="utf-8")

    args = Namespace(
        palette=str(palette_file),
        theme_color="#FF0000",
        page_width=220,
        page_height=300,
    )

    story.when("_build_config_overrides runs")
    overrides = _build_config_overrides(args)

    story.then("all overrides are preserved and no color_scheme is added")
    assert overrides["palette_file"] == str(palette_file)
    assert overrides["theme_color"] == "#FF0000"
    assert overrides["page_width"] == 220
    assert overrides["page_height"] == 300
    assert "color_scheme" not in overrides


def test_build_config_overrides_treats_missing_yaml_as_scheme(
    story, tmp_path: Path
) -> None:
    story.given("the palette path points to a missing YAML file")
    missing_file = tmp_path / "missing.yaml"

    args = Namespace(
        palette=str(missing_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides runs")
    overrides = _build_config_overrides(args)

    story.then("the palette value falls back to color_scheme")
    assert overrides["color_scheme"] == str(missing_file)
    assert "palette_file" not in overrides


def test_build_config_overrides_rejects_yaml_directory(story, tmp_path: Path) -> None:
    story.given("the provided path is a directory ending with .yaml")
    palette_dir = tmp_path / "fake.yaml"
    palette_dir.mkdir()

    args = Namespace(
        palette=str(palette_dir),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides runs")
    overrides = _build_config_overrides(args)

    story.then("directories are treated as scheme names")
    assert overrides["color_scheme"] == str(palette_dir)
    assert "palette_file" not in overrides


def test_build_config_overrides_rejects_yaml_txt(story, tmp_path: Path) -> None:
    story.given("the path ends with .yaml.txt, not a true YAML file")
    bad_file = tmp_path / "palette.yaml.txt"
    bad_file.write_text("palette", encoding="utf-8")

    args = Namespace(
        palette=str(bad_file),
        theme_color=None,
        page_width=None,
        page_height=None,
    )

    story.when("_build_config_overrides runs")
    overrides = _build_config_overrides(args)

    story.then("the suffix check prevents false positives")
    assert overrides["color_scheme"] == str(bad_file)
    assert "palette_file" not in overrides
