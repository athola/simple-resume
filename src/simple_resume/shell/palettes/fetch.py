"""Shell layer palette fetching with network I/O.

This module executes the network operations described by PaletteFetchRequest
objects created by the pure core logic. This isolates all network I/O
to the shell layer.
"""

from typing import Any

from simple_resume.core.palettes import PaletteFetchRequest
from simple_resume.core.palettes.exceptions import PaletteLookupError
from simple_resume.shell.palettes.remote import ColourLoversClient


def execute_palette_fetch(
    request: PaletteFetchRequest,
) -> tuple[list[str], dict[str, Any]]:
    """Shell operation - performs network I/O to fetch palette.

    This function executes the network operation described by the request
    and returns the actual color data.

    Args:
        request: Palette fetch request describing the network operation

    Returns:
        Tuple of (colors, metadata) from the remote source

    Raises:
        PaletteLookupError: If palette fetch fails or returns no results

    """
    if request.source not in {"colourlovers", "remote"}:
        raise PaletteLookupError(f"Unsupported remote source: {request.source}")

    client = ColourLoversClient()
    # Convert list of keywords to comma-separated string for the API
    keywords_str = ",".join(request.keywords) if request.keywords else None
    palettes = client.fetch(
        keywords=keywords_str,
        num_results=request.num_results,
        order_by=request.order_by,
    )

    if not palettes:
        raise PaletteLookupError(f"No palettes found for keywords: {request.keywords}")

    palette = palettes[0]
    colors = list(palette.swatches)

    metadata = {
        "source": request.source,
        "name": palette.name,
        "attribution": palette.metadata,
        "size": len(colors),
    }

    return colors, metadata


__all__ = [
    "execute_palette_fetch",
]
