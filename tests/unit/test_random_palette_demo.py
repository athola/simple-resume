"""Tests for the random palette demo CLI helpers."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from oyaml import safe_load

# Archived from shell.cli to examples/utilities
_demo_path = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "utilities"
    / "random_palette_demo.py"
)
_spec = importlib.util.spec_from_file_location("random_palette_demo", _demo_path)
assert _spec is not None and _spec.loader is not None
demo: types.ModuleType = importlib.util.module_from_spec(_spec)
sys.modules["random_palette_demo"] = demo
_spec.loader.exec_module(demo)
from tests.bdd import Scenario  # noqa: E402


def test_generate_random_yaml_produces_realistic_fields(
    story: Scenario, tmp_path: Path
) -> None:
    story.given("a template YAML with placeholder values")
    story.when("generating random palette demo YAML with a fixed seed")
    template = tmp_path / "template.yaml"
    template.write_text(
        """
full_name: Placeholder
job_title: Placeholder
body:
  Experience:
    - company: ExampleCorp
      description: "-"
      title: Engineer
  Projects:
    - title: Demo
      description: "-"
""",
        encoding="utf-8",
    )

    output = tmp_path / "out.yaml"
    demo.generate_random_yaml(output_path=output, template_path=template, seed=42)

    data = safe_load(output.read_text(encoding="utf-8"))
    assert data["full_name"] != "Placeholder"
    assert "@" in data["email"]
    assert data["config"]["color_scheme"]
    assert output.exists()


def test_main_writes_output_with_seed(
    story: Scenario, tmp_path: Path, monkeypatch
) -> None:
    story.given("CLI entry point is invoked with output and seed arguments")
    story.when("random palette demo main executes")
    output = tmp_path / "cli.yaml"
    template = tmp_path / "template.yaml"
    template.write_text("full_name: Base\nbody: {Experience: []}\n", encoding="utf-8")

    monkeypatch.setenv("PYTHONWARNINGS", "ignore")  # silence oyaml warnings if any
    monkeypatch.setattr(
        "sys.argv",
        [
            "random_palette_demo",
            "--output",
            str(output),
            "--template",
            str(template),
            "--seed",
            "123",
        ],
    )

    demo.main()

    data = safe_load(output.read_text(encoding="utf-8"))
    assert data["full_name"] != "Base"
    assert "color_scheme" in data.get("config", {})
