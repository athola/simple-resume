from __future__ import annotations

import json
from importlib import resources


def test_schema_json_is_packaged_and_valid_json() -> None:
    assets = resources.files("simple_resume") / "shell" / "assets" / "static"
    schema_path = assets / "schema.json"
    assert schema_path.is_file()

    payload = json.loads(schema_path.read_text(encoding="utf-8"))

    assert payload.get("$schema")
    assert payload.get("title")
    assert "config" in payload.get("properties", {})
