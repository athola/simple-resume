"""Theme management for Simple Resume.

This module provides theme loading and application functionality,
allowing users to apply pre-built themes or create custom ones.

Usage in resume YAML:

    # Apply a built-in theme
    theme: modern

    # Override specific theme values
    theme: modern
    config:
      sidebar_width: 70  # Overrides theme default

Available themes: modern, classic, bold, minimal, executive
"""

from simple_resume.shell.themes.loader import (
    apply_theme_to_config,
    clear_theme_cache,
    get_themes_directory,
    list_available_themes,
    load_theme,
    resolve_theme_in_data,
)

__all__ = [
    "apply_theme_to_config",
    "clear_theme_cache",
    "get_themes_directory",
    "list_available_themes",
    "load_theme",
    "resolve_theme_in_data",
]
