from __future__ import annotations

from collections.abc import Callable
from typing import Any

from simple_resume.core.config import normalize_config
from simple_resume.core.palettes.common import Palette
from simple_resume.core.palettes.fetch_types import PaletteFetchRequest
from simple_resume.core.palettes.registry import PaletteRegistry
from simple_resume.shell.palettes.loader import get_palette_registry
from tests.bdd import scenario


def _run_normalize(
    palette_block: dict[str, Any],
    *,
    registry: PaletteRegistry | None = None,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run the config normalization pipeline with a palette block."""
    raw_config: dict[str, Any] = {"palette": palette_block}
    if registry is None:
        registry = get_palette_registry()
    return normalize_config(
        raw_config,
        filename="palette-integration.yaml",
        registry=registry,
        palette_fetcher=palette_fetcher,
    )


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

    registry = PaletteRegistry()
    registry.register(palette)

    story.given("a registry palette named 'Sunset Fiesta' exists")
    normalized, palette_meta = _run_normalize(
        {"source": "registry", "name": "Sunset Fiesta"},
        registry=registry,
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
        "simple_resume.core.palettes.resolution.generate_hcl_palette",
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


def test_palette_processing_remote_source() -> None:
    story = scenario("hydrate palettes from the remote ColourLovers client")

    captured: dict[str, Any] | None = None

    def dummy_fetcher(
        request: PaletteFetchRequest,
    ) -> tuple[list[str], dict[str, Any]]:
        nonlocal captured
        captured = {
            "keywords": request.keywords,
            "num_results": request.num_results,
            "order_by": request.order_by,
        }
        return (
            ["#0A0A0A", "#1B1B1B", "#2C2C2C"],
            {
                "source": "remote",
                "name": "Remote Breeze",
                "size": 3,
                "attribution": {"author": "api"},
            },
        )

    remote_block = {
        "source": "remote",
        "keywords": "calm",
        "num_results": 3,
        "order_by": "dateCreated",
    }

    story.when("normalize_config pulls swatches from the remote source")
    normalized, palette_meta = _run_normalize(
        remote_block,
        palette_fetcher=dummy_fetcher,
    )

    story.then(
        "remote metadata, swatches, and API parameters flow through the pipeline"
    )
    assert captured is not None
    assert captured == {
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
