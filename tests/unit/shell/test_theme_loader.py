"""Tests for theme loading functionality."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from simple_resume.shell.themes import (
    apply_theme_to_config,
    clear_theme_cache,
    get_themes_directory,
    list_available_themes,
    load_theme,
    resolve_theme_in_data,
)


@pytest.fixture(autouse=True)
def clear_cache() -> Generator[None, None, None]:
    """Clear theme cache before and after each test."""
    clear_theme_cache()
    yield
    clear_theme_cache()


class TestThemesDirectory:
    """Tests for theme directory discovery."""

    def test_get_themes_directory_returns_path(self) -> None:
        """Theme directory path should be returned."""
        themes_dir = get_themes_directory()
        assert themes_dir.exists()
        assert themes_dir.is_dir()

    def test_themes_directory_contains_yaml_files(self) -> None:
        """Theme directory should contain YAML theme files."""
        themes_dir = get_themes_directory()
        yaml_files = list(themes_dir.glob("*.yaml"))
        assert len(yaml_files) > 0, "No theme files found"


class TestListAvailableThemes:
    """Tests for listing available themes."""

    def test_list_available_themes_returns_list(self) -> None:
        """Should return a list of theme names."""
        themes = list_available_themes()
        assert isinstance(themes, list)
        assert len(themes) > 0

    def test_list_available_themes_includes_builtin_themes(self) -> None:
        """Should include the built-in themes."""
        themes = list_available_themes()
        expected = {"modern", "classic", "bold", "minimal", "executive"}
        assert expected.issubset(set(themes))

    def test_list_available_themes_excludes_readme(self) -> None:
        """Should not include README in theme list."""
        themes = list_available_themes()
        assert "README" not in themes


class TestLoadTheme:
    """Tests for loading individual themes."""

    def test_load_theme_returns_config_dict(self) -> None:
        """Should return a configuration dictionary."""
        config = load_theme("modern")
        assert isinstance(config, dict)

    def test_load_theme_contains_palette(self) -> None:
        """Theme config should contain palette settings."""
        config = load_theme("modern")
        assert "palette" in config

    def test_load_theme_contains_dimensions(self) -> None:
        """Theme config should contain dimension settings."""
        config = load_theme("modern")
        assert "page_width" in config
        assert "page_height" in config

    def test_load_nonexistent_theme_raises_error(self) -> None:
        """Loading non-existent theme should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_theme("nonexistent_theme_xyz")


class TestApplyThemeToConfig:
    """Tests for applying themes to user configuration."""

    def test_apply_theme_returns_merged_config(self) -> None:
        """Should return merged configuration."""
        user_config = {"sidebar_width": 70}
        result = apply_theme_to_config(user_config, "modern")

        # Should have both theme and user values
        assert "palette" in result  # from theme
        assert result["sidebar_width"] == 70  # user override

    def test_user_config_overrides_theme(self) -> None:
        """User configuration should override theme defaults."""
        theme_config = load_theme("modern")
        original_sidebar_width = theme_config.get("sidebar_width", 60)

        user_config = {"sidebar_width": 100}
        result = apply_theme_to_config(user_config, "modern")

        assert result["sidebar_width"] == 100
        assert result["sidebar_width"] != original_sidebar_width

    def test_apply_invalid_theme_returns_user_config(self) -> None:
        """Invalid theme should return user config unchanged."""
        user_config = {"sidebar_width": 70}
        result = apply_theme_to_config(user_config, "nonexistent")
        assert result == user_config


class TestResolveThemeInData:
    """Tests for resolving theme references in resume data."""

    def test_resolve_theme_from_top_level(self) -> None:
        """Should resolve theme from top-level 'theme' key."""
        data = {
            "full_name": "Test User",
            "theme": "modern",
            "config": {"sidebar_width": 70},
        }

        result = resolve_theme_in_data(data)

        # Theme should be removed from result
        assert "theme" not in result
        # Config should have theme values merged
        assert "palette" in result["config"]
        # User override should be preserved
        assert result["config"]["sidebar_width"] == 70

    def test_resolve_theme_from_config_block(self) -> None:
        """Should resolve theme from config block."""
        data = {
            "full_name": "Test User",
            "config": {
                "theme": "classic",
                "sidebar_width": 70,
            },
        }

        result = resolve_theme_in_data(data)

        # Config should have theme values merged
        assert "palette" in result["config"]
        # User override should be preserved
        assert result["config"]["sidebar_width"] == 70

    def test_resolve_no_theme_returns_unchanged(self) -> None:
        """Data without theme should be returned unchanged."""
        data = {
            "full_name": "Test User",
            "config": {"sidebar_width": 70},
        }

        result = resolve_theme_in_data(data)

        assert result == data

    def test_resolve_preserves_non_config_keys(self) -> None:
        """Should preserve all non-config keys in data."""
        data = {
            "full_name": "Test User",
            "job_title": "Developer",
            "theme": "modern",
            "body": {"Experience": []},
        }

        result = resolve_theme_in_data(data)

        assert result["full_name"] == "Test User"
        assert result["job_title"] == "Developer"
        assert result["body"] == {"Experience": []}
