"""Test schema.json defaults match config.py apply_config_defaults() defaults.

This test prevents drift between the JSON schema used for validation
and the Python defaults used at runtime. When schema.json is updated
with new defaults, config.py should be updated to match (or vice versa).

This catches cases where:
- schema.json default is updated but config.py is not (or vice versa)
- Documentation (schema) doesn't match runtime behavior (Python defaults)
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

import pytest

from simple_resume.core.config import apply_config_defaults
from tests.bdd import scenario


def _load_schema() -> dict[str, Any]:
    """Load and parse the schema.json file."""
    assets = resources.files("simple_resume") / "shell" / "assets" / "static"
    schema_path = assets / "schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _get_schema_config_defaults() -> dict[str, Any]:
    """Extract config defaults from schema.json.

    Returns a dict mapping property names to their default values
    as defined in the schema's $defs/config section.
    """
    schema = _load_schema()
    config_def = schema.get("$defs", {}).get("config", {})
    config_properties = config_def.get("properties", {})

    defaults: dict[str, Any] = {}
    for prop_name, prop_def in config_properties.items():
        if "default" in prop_def:
            defaults[prop_name] = prop_def["default"]
    return defaults


def test_schema_defaults_match_config_defaults() -> None:
    """Verify schema.json defaults match apply_config_defaults() output.

    This test ensures that defaults defined in schema.json match the
    defaults applied by apply_config_defaults() in config.py. Drift
    between these two sources leads to confusing behavior where
    validation accepts one value but runtime uses another.

    Note: We only check properties that ARE defined in apply_config_defaults().
    Schema may have additional defaults (like template, color_scheme) that
    are handled by other parts of the codebase.
    """
    story = scenario("schema defaults match config.py defaults")
    story.given("an empty config dictionary and the loaded schema defaults")

    schema_defaults = _get_schema_config_defaults()
    config: dict[str, Any] = {}

    story.when("apply_config_defaults is called on the empty config")
    apply_config_defaults(config)

    story.then("all schema defaults match the applied Python defaults")

    # Only check properties that exist in config after defaults are applied
    # (i.e., properties that apply_config_defaults actually sets)
    mismatches: list[tuple[str, Any, Any]] = []

    for prop_name, config_default in config.items():
        if prop_name not in schema_defaults:
            continue

        schema_default = schema_defaults[prop_name]

        # Compare defaults (handle float/int equivalence)
        try:
            if float(schema_default) != float(config_default):
                mismatches.append(
                    (
                        prop_name,
                        schema_default,
                        config_default,
                    )
                )
        except (TypeError, ValueError):
            # Non-numeric comparison
            if schema_default != config_default:
                mismatches.append(
                    (
                        prop_name,
                        schema_default,
                        config_default,
                    )
                )

    # Build detailed assertion message
    if mismatches:
        mismatch_lines = [
            f"\n  - {prop}: schema={schema_val!r}, config={config_val!r}"
            for prop, schema_val, config_val in mismatches
        ]
        pytest.fail(
            f"Schema defaults do not match config.py defaults for {len(mismatches)} "
            f"properties:{''.join(mismatch_lines)}\n\n"
            f"Update either schema.json or config.py:apply_config_defaults() "
            f"to ensure consistency."
        )


def test_schema_font_size_defaults_match_config() -> None:
    """Specifically verify font size defaults match between schema and config.

    This is a targeted test for the font size properties that were
    identified as important during PR #41 review (sidebar_font_size,
    description_font_size, date_font_size).
    """
    story = scenario("font size defaults match between schema and config")
    story.given("empty config and schema with font size properties")

    schema_defaults = _get_schema_config_defaults()
    config: dict[str, Any] = {}

    story.when("apply_config_defaults is called")
    apply_config_defaults(config)

    story.then("font size defaults match exactly")

    font_size_props = {
        "sidebar_font_size": 8.5,
        "description_font_size": 8.5,
        "date_font_size": 9.0,
    }

    for prop_name, expected_default in font_size_props.items():
        schema_default = schema_defaults.get(prop_name)
        config_default = config.get(prop_name)

        assert schema_default == expected_default, (
            f"schema.json {prop_name} default should be {expected_default}, "
            f"got {schema_default}"
        )
        assert config_default == expected_default, (
            f"config.py {prop_name} default should be {expected_default}, "
            f"got {config_default}"
        )


def test_schema_numeric_defaults_with_tolerance() -> None:
    """Verify numeric defaults match within floating point tolerance.

    Some schema defaults may be floats while Python defaults are ints
    (or vice versa). This test allows for type equivalence as long as
    the numeric values are the same.
    """
    story = scenario("numeric defaults match within tolerance")
    story.given("empty config and loaded schema")

    schema_defaults = _get_schema_config_defaults()
    config: dict[str, Any] = {}

    story.when("apply_config_defaults is called")
    apply_config_defaults(config)

    story.then("numeric defaults are equivalent (int/float tolerance)")

    numeric_types = (int, float)

    for prop_name, schema_default in schema_defaults.items():
        # Only check numeric properties
        if not isinstance(schema_default, numeric_types):
            continue

        if prop_name not in config:
            pytest.fail(
                f"Property {prop_name} has schema default {schema_default} "
                f"but is missing from config.py defaults"
            )

        config_default = config[prop_name]

        if not isinstance(config_default, numeric_types):
            pytest.fail(
                f"Property {prop_name}: schema default is numeric ({schema_default}) "
                f"but config default is {type(config_default).__name__} "
                f"({config_default})"
            )

        # Compare with tolerance for floating point
        assert abs(float(schema_default) - float(config_default)) < 1e-9, (
            f"Property {prop_name}: numeric mismatch - "
            f"schema={schema_default}, config={config_default}"
        )
