from __future__ import annotations

from typing import Any

from simple_resume.palettes.common import Palette
from simple_resume.utilities import normalize_config
from tests.bdd import scenario


def _run_normalize(
    palette_block: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run the config normalization pipeline with a palette block."""
    raw_config: dict[str, Any] = {"palette": palette_block}
    return normalize_config(raw_config, filename="palette-integration.yaml")


def test_palette_processing_direct_colors() -> None:
    story = scenario("apply direct color overrides without palette lookup")
    story.given("the resume config includes a palette block with explicit colors")
    direct_palette = {
        "theme_color": "#101010",
        "sidebar_color": "#EFEFEF",
        "bar_background_color": "#222222",
        "date2_color": "#333333",
        "frame_color": "#444444",
        "heading_icon_color": "#555555",
        "bold_color": "#666666",
        "sidebar_bold_color": "#777777",
    }

    story.when("normalize_config runs through the palette application pipeline")
    normalized, palette_meta = _run_normalize(direct_palette)

    story.then(
        "direct color metadata is returned and colors persist through finalize_config"
    )
    assert palette_meta is not None
    assert palette_meta["source"] == "direct"
    assert set(palette_meta["fields"]) >= {
        "theme_color",
        "sidebar_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
        "heading_icon_color",
        "bold_color",
        "sidebar_bold_color",
    }
    assert normalized["theme_color"] == "#101010"
    assert normalized["bold_color"] == "#666666"
    assert normalized["sidebar_bold_color"] == "#777777"


def test_palette_processing_registry_source(monkeypatch: Any) -> None:
    story = scenario("resolve palettes from the registry source")
    swatches = ("#123123", "#234234", "#345345")
    palette = Palette(
        name="Sunset Fiesta",
        swatches=swatches,
        source="registry",
        metadata={"curator": "integration-test"},
    )

    class DummyRegistry:
        def get(self, name: str) -> Palette:
            assert name == "Sunset Fiesta"
            return palette

    story.given("a registry palette named 'Sunset Fiesta' exists")
    monkeypatch.setattr(
        "simple_resume.core.config_core.get_palette_registry",
        lambda: DummyRegistry(),
    )

    story.when("normalize_config requests palette colors from the registry")
    normalized, palette_meta = _run_normalize(
        {"source": "registry", "name": "Sunset Fiesta"}
    )

    story.then("registry metadata and swatches hydrate the configuration")
    assert palette_meta is not None
    assert palette_meta["source"] == "registry"
    assert palette_meta["name"] == palette.name
    assert palette_meta["size"] == len(swatches)
    assert normalized["theme_color"] == swatches[0]
    assert normalized["sidebar_color"] == swatches[1]


def test_palette_processing_generator_source(monkeypatch: Any) -> None:
    story = scenario("generate palettes procedurally with deterministic swatches")
    stub_swatches = [
        "#111111",
        "#222222",
        "#333333",
        "#444444",
        "#555555",
        "#666666",
        "#777777",
    ]
    story.given("the HCL palette generator returns a deterministic sequence")
    monkeypatch.setattr(
        "simple_resume.core.config_core.generate_hcl_palette",
        lambda *args, **kwargs: list(stub_swatches),
    )

    generator_block = {
        "source": "generator",
        "size": 7,
        "seed": 123,
        "hue_range": (10, 80),
        "luminance_range": (0.2, 0.9),
        "chroma": 0.4,
    }

    story.when("normalize_config requests colors from the generator source")
    normalized, palette_meta = _run_normalize(generator_block)

    story.then("generator metadata includes the requested parameters")
    assert palette_meta is not None
    assert palette_meta["source"] == "generator"
    assert palette_meta["size"] == len(stub_swatches)
    assert palette_meta["seed"] == 123
    assert palette_meta["hue_range"] == [10.0, 80.0]
    assert palette_meta["luminance_range"] == [0.2, 0.9]
    assert palette_meta["chroma"] == 0.4
    assert normalized["theme_color"] == stub_swatches[0]


def test_palette_processing_remote_source(monkeypatch: Any) -> None:
    story = scenario("hydrate palettes from the remote ColourLovers client")

    class DummyClient:
        def __init__(self) -> None:
            self.params: dict[str, Any] | None = None

        def fetch(self, **kwargs: Any) -> list[Palette]:
            self.params = kwargs
            return [
                Palette(
                    name="Remote Breeze",
                    swatches=("#0A0A0A", "#1B1B1B", "#2C2C2C"),
                    source="colourlovers",
                    metadata={"id": 42, "author": "api"},
                )
            ]

    dummy_client = DummyClient()
    story.given("the remote client returns a stable palette payload")
    monkeypatch.setattr(
        "simple_resume.core.config_core.ColourLoversClient",
        lambda: dummy_client,
    )

    remote_block = {
        "source": "remote",
        "keywords": "calm",
        "num_results": 3,
        "order_by": "dateCreated",
    }

    story.when("normalize_config pulls swatches from the remote source")
    normalized, palette_meta = _run_normalize(remote_block)

    story.then(
        "remote metadata, swatches, and API parameters flow through the pipeline"
    )
    assert dummy_client.params == {
        "keywords": "calm",
        "num_results": 3,
        "order_by": "dateCreated",
    }
    assert palette_meta is not None
    assert palette_meta["source"] == "remote"
    assert palette_meta["name"] == "Remote Breeze"
    assert palette_meta["size"] == 3
    assert palette_meta["attribution"]["author"] == "api"
    assert normalized["theme_color"] == "#0A0A0A"
