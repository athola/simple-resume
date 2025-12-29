"""Theme loading operations (shell layer with I/O).

This module handles loading theme presets from the themes directory
and merging them with user configuration.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Theme directory relative to assets
THEME_DIR_NAME = "themes"


def get_themes_directory() -> Path:
    """Get the path to the bundled themes directory."""
    # Late import to avoid circular dependency
    from simple_resume.shell.config import ASSETS_ROOT  # noqa: PLC0415

    return ASSETS_ROOT / "static" / THEME_DIR_NAME


def list_available_themes() -> list[str]:
    """List all available theme names.

    Returns:
        List of theme names (without .yaml extension).

    """
    themes_dir = get_themes_directory()
    if not themes_dir.exists():
        return []

    return sorted(p.stem for p in themes_dir.glob("*.yaml") if p.stem != "README")


@lru_cache(maxsize=32)
def _load_theme_file(theme_path: Path) -> dict[str, Any]:
    """Load and cache a theme file.

    Args:
        theme_path: Path to the theme YAML file.

    Returns:
        Theme configuration dictionary.

    Raises:
        FileNotFoundError: If theme file doesn't exist.
        ValueError: If theme file is invalid YAML.

    """
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme file not found: {theme_path}")

    try:
        with theme_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid theme YAML: {theme_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Theme file must contain a dictionary: {theme_path}")

    return data


def load_theme(theme_name: str) -> dict[str, Any]:
    """Load a theme by name.

    Args:
        theme_name: Name of the theme (without .yaml extension).

    Returns:
        Theme configuration dictionary (the 'config' block).

    Raises:
        FileNotFoundError: If theme doesn't exist.
        ValueError: If theme file is invalid or theme name contains path traversal.

    """
    themes_dir = get_themes_directory()
    theme_path = (themes_dir / f"{theme_name}.yaml").resolve()

    # Validate path stays within themes directory (prevent path traversal)
    if not theme_path.is_relative_to(themes_dir.resolve()):
        raise ValueError(f"Invalid theme name: {theme_name}")

    theme_data = _load_theme_file(theme_path)

    # Return just the config block if present, otherwise return the whole dict
    if "config" in theme_data:
        return dict(theme_data["config"])

    return dict(theme_data)


class ThemeLoadError(Exception):
    """Raised when theme loading fails in strict mode."""


def apply_theme_to_config(
    user_config: dict[str, Any],
    theme_name: str,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Apply a theme to user configuration.

    Theme values are used as defaults - user values take precedence.

    Args:
        user_config: User's configuration dictionary.
        theme_name: Name of the theme to apply.
        strict: If True, raise ThemeLoadError on failure instead of falling back.

    Returns:
        Merged configuration with theme defaults and user overrides.

    Raises:
        ThemeLoadError: If strict=True and theme loading fails.

    """
    try:
        theme_config = load_theme(theme_name)
    except (FileNotFoundError, ValueError) as exc:
        if strict:
            raise ThemeLoadError(f"Failed to load theme '{theme_name}': {exc}") from exc
        logger.warning("Failed to load theme '%s': %s", theme_name, exc)
        return user_config

    # Deep merge: theme provides defaults, user overrides
    merged = _deep_merge(theme_config, user_config)

    logger.debug("Applied theme '%s' to configuration", theme_name)
    return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Values from override take precedence. Nested dicts are merged recursively.

    Args:
        base: Base dictionary (theme defaults).
        override: Override dictionary (user config).

    Returns:
        Merged dictionary.

    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def resolve_theme_in_data(data: dict[str, Any]) -> dict[str, Any]:
    """Resolve theme reference in resume data.

    If the data contains a 'theme' key at the top level or in 'config',
    loads the theme and merges it with existing config.

    Args:
        data: Resume data dictionary.

    Returns:
        Data with theme applied to config.

    """
    # Check for theme at top level
    theme_name = data.get("theme")

    # Also check inside config block
    config = data.get("config", {})
    if isinstance(config, dict) and "theme" in config:
        theme_name = config.get("theme")

    if not theme_name:
        return data

    if not isinstance(theme_name, str):
        logger.warning("Invalid theme value: %s (expected string)", theme_name)
        return data

    # Load theme and merge with config
    result = data.copy()
    existing_config = result.get("config", {})
    if not isinstance(existing_config, dict):
        existing_config = {}

    # Remove theme key from config (it's been processed)
    existing_config = {k: v for k, v in existing_config.items() if k != "theme"}

    # Apply theme (theme provides defaults, user config overrides)
    merged_config = apply_theme_to_config(existing_config, theme_name)

    result["config"] = merged_config

    # Remove top-level theme key if present
    result.pop("theme", None)

    return result


def clear_theme_cache() -> None:
    """Clear the theme file cache (for testing)."""
    _load_theme_file.cache_clear()


__all__ = [
    "ThemeLoadError",
    "apply_theme_to_config",
    "clear_theme_cache",
    "get_themes_directory",
    "list_available_themes",
    "load_theme",
    "resolve_theme_in_data",
]
