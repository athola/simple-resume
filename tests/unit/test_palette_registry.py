from __future__ import annotations

import pytest

from simple_resume.palettes.registry import (
    Palette,
    PaletteRegistry,
    get_palette_registry,
    reset_palette_registry,
)
from simple_resume.palettes.sources import PalettableRecord, load_default_palettes
from tests.bdd import Scenario


def test_load_default_palettes_returns_palettes(story: Scenario) -> None:
    story.given("the built-in palette catalogue is requested")
    palettes = load_default_palettes()

    story.then("at least one palette with swatches is returned")
    assert palettes, "Expected at least one default palette"
    assert all(palette.swatches for palette in palettes)


def test_palette_registry_register_and_get(story: Scenario) -> None:
    story.given("an empty registry and a palette to register")
    registry = PaletteRegistry()
    palette = Palette(name="Test", swatches=("#FFFFFF",), source="test")

    story.when("the palette is registered")
    registry.register(palette)

    story.then("the palette can be retrieved case-insensitively")
    assert registry.get("test") == palette
    with pytest.raises(KeyError):
        registry.get("missing")


def test_global_registry_uses_palettable(
    story: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = PalettableRecord(
        name="Mock Palette",
        module="palettable.colorbrewer.sequential",
        attribute="Blues_3",
        category="sequential",
        palette_type="sequential",
        size=3,
    )

    def fake_ensure() -> list[PalettableRecord]:
        return [record]

    def fake_load(_: PalettableRecord) -> Palette:
        return Palette(
            name="Mock Palette", swatches=("#000000", "#111111"), source="palettable"
        )

    monkeypatch.setattr(
        "simple_resume.palettes.registry.ensure_bundled_palettes_loaded", fake_ensure
    )
    monkeypatch.setattr(
        "simple_resume.palettes.registry.load_palettable_palette", fake_load
    )
    reset_palette_registry()

    story.when("the global registry is first initialised")
    registry = get_palette_registry()

    story.then("palettable-backed palettes are registered and retrievable")
    palette = registry.get("mock palette")
    assert palette.source == "palettable"
    assert len(palette.swatches) == 2
