#!/usr/bin/env python3
"""Provide procedural palette generators."""

from __future__ import annotations

import colorsys
import hashlib
import math

# Default deterministic seed for consistent color palette generation
# Format: YYYYMMDD (November 1, 2025) - ensures reproducible palettes across runs
DEFAULT_SEED = 20251101


class DeterministicRNG:
    """Define a deterministic random number generator using hash-based seeding."""

    def __init__(self, seed: int):
        """Initialize the deterministic RNG with a seed.

        Args:
            seed: The seed for the random number generator.

        """
        self.seed = seed
        self.state = seed

    def random(self) -> float:
        """Generate a deterministic random float between 0 and 1."""
        self.state += 1
        hash_input = f"{self.seed}-{self.state}".encode()
        # 64-bit digest keeps deterministic behavior without wasting work
        hash_bytes = hashlib.blake2s(hash_input, digest_size=8).digest()
        hash_int = int.from_bytes(hash_bytes, "big")
        return hash_int / (2**64 - 1)

    def uniform(self, a: float, b: float) -> float:
        """Generate a deterministic random float between a and b."""
        return a + self.random() * (b - a)


def _clamp(value: float, low: float, high: float) -> float:
    """Restrict a value to the [low, high] interval."""
    return max(low, min(value, high))


def _wrap_hue(value: float) -> float:
    """Wrap a hue value into [0, 360) degrees."""
    return value % 360.0


def _generate_hues(
    *,
    start: float,
    end: float,
    count: int,
    rng: DeterministicRNG,
) -> list[float]:
    """Return evenly distributed hues between start and end (inclusive)."""
    start = _wrap_hue(start)
    end = _wrap_hue(end)

    if count == 1:
        return [start]

    span = (end - start) % 360.0
    if math.isclose(span, 0.0):
        span = 360.0

    step = span / (count - 1)
    return [
        _wrap_hue(start + index * step + rng.uniform(-step * 0.05, step * 0.05))
        for index in range(count)
    ]


def _generate_luminance_values(
    *,
    start: float,
    end: float,
    count: int,
) -> list[float]:
    """Return interpolated luminance values."""
    if count == 1:
        return [_clamp(start, 0.0, 1.0)]
    step = (end - start) / (count - 1)
    return [_clamp(start + index * step, 0.0, 1.0) for index in range(count)]


def _hsl_to_hex(hue: float, saturation: float, luminance: float) -> str:
    """Convert HSL values to a hex string."""
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, luminance, saturation)
    r_hex = f"{int(_clamp(r, 0.0, 1.0) * 255 + 0.5):02X}"
    g_hex = f"{int(_clamp(g, 0.0, 1.0) * 255 + 0.5):02X}"
    b_hex = f"{int(_clamp(b, 0.0, 1.0) * 255 + 0.5):02X}"
    return f"#{r_hex}{g_hex}{b_hex}"


def generate_hcl_palette(
    size: int,
    *,
    seed: int | None = None,
    hue_range: tuple[float, float] = (0.0, 360.0),
    chroma: float = 0.12,
    luminance_range: tuple[float, float] = (0.35, 0.85),
) -> list[str]:
    """Generate a deterministic palette in an HCL-inspired fashion.

    Args:
        size: Number of swatches to produce.
        seed: Optional deterministic seed. Defaults to a project seed.
        hue_range: Inclusive range of hue values (degrees).
        chroma: Saturation component (0-1, approximated using HSL saturation).
        luminance_range: Inclusive range of luminance/lightness values.

    Returns:
        List of hex color strings.

    """
    if size <= 0:
        raise ValueError("size must be a positive integer")

    rng = DeterministicRNG(seed if seed is not None else DEFAULT_SEED)
    hue_start, hue_end = hue_range
    lum_start, lum_end = luminance_range

    hues = _generate_hues(start=hue_start, end=hue_end, count=size, rng=rng)
    luminances = _generate_luminance_values(start=lum_start, end=lum_end, count=size)

    saturation = _clamp(chroma, 0.0, 1.0)
    colors: list[str] = []
    for hue, luminance in zip(hues, luminances):
        colors.append(_hsl_to_hex(hue, saturation, _clamp(luminance, 0.0, 1.0)))
    return colors


__all__ = ["generate_hcl_palette"]
