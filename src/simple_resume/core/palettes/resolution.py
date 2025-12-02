"""Pure palette resolution logic without network I/O.

This module contains pure functions that resolve palette configurations
into either colors or fetch requests, without performing any I/O operations.
"""

from typing import Any

from simple_resume.core.constants.colors import CONFIG_COLOR_FIELDS
from simple_resume.core.palettes.common import PaletteSource
from simple_resume.core.palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
)
from simple_resume.core.palettes.fetch_types import (
    PaletteFetchRequest,
    PaletteResolution,
)
from simple_resume.core.palettes.generators import generate_hcl_palette
from simple_resume.core.palettes.registry import PaletteRegistry


def resolve_palette_config(
    block: dict[str, Any], *, registry: PaletteRegistry
) -> PaletteResolution:
    """Pure palette resolution - returns colors OR fetch request.

    This function performs pure logic to determine what colors are needed
    and how to obtain them. It never performs I/O operations.

    Args:
        block: Palette configuration block from resume config.
        registry: Palette registry to look up named palettes (injected dependency).

    Returns:
        PaletteResolution with either colors (for local sources) or
        a fetch request (for remote sources).

    Raises:
        PaletteError: If palette configuration is invalid.

    """
    try:
        source = PaletteSource.normalize(block.get("source"), param_name="palette")
    except (TypeError, ValueError) as exc:
        raise PaletteError(
            f"Unsupported palette source: {block.get('source')}"
        ) from exc

    if source is PaletteSource.REGISTRY:
        """Pure lookup from local registry (no I/O)."""
        name = block.get("name")
        if not name:
            raise PaletteLookupError("registry source requires 'name'")

        palette = registry.get(str(name))

        colors = list(palette.swatches)
        metadata = {
            "source": source.value,
            "name": palette.name,
            "size": len(palette.swatches),
            "attribution": palette.metadata,
        }

        return PaletteResolution(colors=colors, metadata=metadata)

    elif source is PaletteSource.GENERATOR:
        """Pure generation - no I/O."""

        size = int(block.get("size", len(CONFIG_COLOR_FIELDS)))
        seed = block.get("seed")
        hue_range = tuple(block.get("hue_range", (0, 360)))
        luminance_range = tuple(block.get("luminance_range", (0.35, 0.85)))
        chroma = float(block.get("chroma", 0.12))

        REQUIRED_RANGE_LENGTH = 2
        if (
            len(hue_range) != REQUIRED_RANGE_LENGTH
            or len(luminance_range) != REQUIRED_RANGE_LENGTH
        ):
            raise PaletteGenerationError(
                "hue_range and luminance_range must have two values"
            )

        colors = generate_hcl_palette(
            size,
            seed=int(seed) if seed is not None else None,
            hue_range=(float(hue_range[0]), float(hue_range[1])),
            chroma=chroma,
            luminance_range=(float(luminance_range[0]), float(luminance_range[1])),
        )

        metadata = {
            "source": source.value,
            "size": len(colors),
            "seed": int(seed) if seed is not None else None,
            "hue_range": [float(hue_range[0]), float(hue_range[1])],
            "luminance_range": [float(luminance_range[0]), float(luminance_range[1])],
            "chroma": chroma,
        }

        return PaletteResolution(colors=colors, metadata=metadata)

    elif source is PaletteSource.REMOTE:
        """Return request for shell to execute - no network I/O here."""
        fetch_request = PaletteFetchRequest(
            source=source.value,
            keywords=block.get("keywords"),
            num_results=int(block.get("num_results", 1)),
            order_by=str(block.get("order_by", "score")),
        )

        return PaletteResolution(fetch_request=fetch_request)

    else:
        raise PaletteError(f"Unsupported palette source: {source.value}")


__all__ = [
    "resolve_palette_config",
]
