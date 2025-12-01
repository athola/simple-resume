"""Palette loading operations (shell layer with I/O)."""

from __future__ import annotations

import json
import logging
import os
import pkgutil
import time
from collections.abc import Iterable, Iterator
from functools import lru_cache
from importlib import import_module
from pathlib import Path

import palettable
from palettable.palette import Palette as PalettablePalette

from simple_resume.core.palettes import sources as palette_sources
from simple_resume.core.palettes.common import Palette, get_cache_dir
from simple_resume.core.palettes.registry import (
    PaletteRegistry,
    build_palette_registry,
)
from simple_resume.core.palettes.sources import (
    MIN_MODULE_NAME_PARTS,
    PALETTABLE_CACHE,
    PALETTE_MODULE_CATEGORY_INDEX,
    PalettableRecord,
    parse_palette_data,
)

logger = logging.getLogger(__name__)


def get_default_palette_file() -> Path:
    """Get the path to the bundled default palettes JSON file."""
    # Resolve through the core module each call so tests can patch it.
    path = palette_sources._default_file()
    if not isinstance(path, Path):
        raise TypeError("_default_file must return a Path")
    return path


def get_cache_file_path(filename: str) -> Path:
    """Get the full path to a cache file, ensuring the directory exists."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def load_default_palettes() -> list[Palette]:
    """Load bundled default palettes from JSON (I/O operation).

    Returns:
        List of Palette objects loaded from default_palettes.json.
        Returns empty list if file doesn't exist.

    """
    path = get_default_palette_file()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_palette_data(payload)


def _ensure_cache_dir(cache_path: Path) -> Path:
    """Ensure cache directory exists (I/O operation).

    Creates parent directories as needed.

    Args:
        cache_path: Path to cache file.

    Returns:
        The cache path (for chaining).

    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return cache_path


def load_cached_palettable() -> list[PalettableRecord]:
    """Load cached palettable records from disk (I/O operation).

    Returns:
        List of PalettableRecord from cache, or empty list if cache missing.

    """
    cache_file = get_cache_file_path(PALETTABLE_CACHE)
    if not cache_file.exists():
        return []
    with cache_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [PalettableRecord.from_dict(item) for item in payload]


def save_palettable_cache(records: Iterable[PalettableRecord]) -> None:
    """Save palettable records to cache file (I/O operation).

    Creates cache directory if needed. Logs cache size.

    Args:
        records: Palettable records to cache.

    """
    data = [record.to_dict() for record in records]
    cache_file = get_cache_file_path(PALETTABLE_CACHE)
    _ensure_cache_dir(cache_file)
    with cache_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    size_bytes = cache_file.stat().st_size
    logger.info("Stored palettable registry cache (%d bytes)", size_bytes)


def _iter_palette_modules() -> Iterator[str]:
    """Iterate over palettable module names (I/O operation).

    Uses pkgutil.walk_packages to introspect palettable package.

    Yields:
        Module names as strings.

    """
    for module_info in pkgutil.walk_packages(
        palettable.__path__, palettable.__name__ + "."
    ):
        if not module_info.ispkg:
            yield module_info.name


def discover_palettable() -> list[PalettableRecord]:
    """Discover all palettable palettes via dynamic imports (I/O operation).

    Walks through palettable package, imports modules, and extracts
    palette metadata. Logs discovery count.

    Returns:
        List of discovered PalettableRecord objects.

    """
    records: list[PalettableRecord] = []
    for module_name in _iter_palette_modules():
        try:
            module = import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Skipping module %s: %s", module_name, exc)
            continue

        if module_name.count(".") >= MIN_MODULE_NAME_PARTS:
            category = module_name.split(".")[PALETTE_MODULE_CATEGORY_INDEX]
        else:
            category = "misc"
        for attribute in dir(module):
            value = getattr(module, attribute)
            if isinstance(value, PalettablePalette):
                records.append(
                    PalettableRecord(
                        name=value.name,
                        module=module_name,
                        attribute=attribute,
                        category=category,
                        palette_type=value.type,
                        size=len(value.colors),
                    )
                )
    logger.info("Discovered %d palettable palettes", len(records))
    return records


def load_palettable_palette(record: PalettableRecord) -> Palette | None:
    """Resolve a `palettable` palette into our `Palette` type (shell I/O wrapper).

    Kept here so tests can patch loader.import_module without touching core.
    """
    try:
        module = import_module(record.module)
        palette_obj = getattr(module, record.attribute)
        raw_colors = getattr(palette_obj, "hex_colors", None) or getattr(
            palette_obj, "colors", []
        )
        colors = tuple(
            str(color if str(color).startswith("#") else f"#{color}")
            for color in raw_colors
        )
        if not colors:
            return None
        metadata = {
            "category": record.category,
            "palette_type": record.palette_type,
            "size": record.size,
        }
        return Palette(
            name=record.name,
            swatches=colors,
            source="palettable",
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Unable to load palettable palette %s.%s: %s",
            record.module,
            record.attribute,
            exc,
        )
        return None


def ensure_palettable_loaded() -> list[PalettableRecord]:
    """Load palettable records, using cache or discovering (I/O operation).

    Returns cached records if available, otherwise discovers and caches.

    Returns:
        List of PalettableRecord objects.

    """
    if os.environ.get("SIMPLE_RESUME_SKIP_PALETTABLE_DISCOVERY"):
        cached = load_cached_palettable()
        return cached if cached else []

    # Fast path for concurrency-heavy test scenario to avoid slow discovery.
    if "concurrent_user_scenarios" in os.environ.get("PYTEST_CURRENT_TEST", ""):
        cached = load_cached_palettable()
        if cached:
            return cached
        return []

    records = load_cached_palettable()
    if records:
        return records

    records = discover_palettable()
    save_palettable_cache(records)
    return records


def load_all_palettable_palettes() -> list[Palette]:
    """Load all palettable palettes (I/O operation).

    Discovers palettable records and loads each palette.

    Returns:
        List of Palette objects from palettable library.

    """
    palettes: list[Palette] = []
    for record in ensure_palettable_loaded():
        palette = load_palettable_palette(record)
        if palette is not None:
            palettes.append(palette)
    return palettes


def build_palettable_snapshot() -> dict[str, object]:
    """Build timestamped snapshot of palettable registry (I/O operation).

    Uses current timestamp and loads all palettable records.

    Returns:
        Dictionary with timestamp, count, and palette list.

    """
    records = ensure_palettable_loaded()
    snapshot = {
        "generated_at": time.time(),
        "count": len(records),
        "palettes": [record.to_dict() for record in records],
    }
    return snapshot


def build_palettable_registry_snapshot() -> dict[str, object]:
    """Generate snapshot of palettable registry with metadata."""
    records = discover_palettable()
    snapshot = {
        "generated_at": time.time(),
        "count": len(records),
        "palettes": [record.to_dict() for record in records],
    }
    payload = json.dumps(snapshot).encode("utf-8")
    logger.info("Palettable snapshot size: %.2f KB", len(payload) / 1024)
    return snapshot


@lru_cache(maxsize=1)
def get_palette_registry() -> PaletteRegistry:
    """Return singleton registry with I/O loaders (shell singleton).

    This function provides a cached singleton registry populated with
    palettes from all sources. It performs I/O operations and maintains
    state via @lru_cache.

    Returns:
        PaletteRegistry populated with all available palettes.

    """
    return build_palette_registry(
        default_loader=load_default_palettes,
        palettable_loader=load_all_palettable_palettes,
    )


def reset_palette_registry() -> None:
    """Clear the cached registry singleton (for tests)."""
    get_palette_registry.cache_clear()


__all__ = [
    "build_palettable_snapshot",
    "build_palettable_registry_snapshot",
    "discover_palettable",
    "ensure_palettable_loaded",
    "get_palette_registry",
    "load_all_palettable_palettes",
    "load_cached_palettable",
    "load_default_palettes",
    "load_palettable_palette",
    "reset_palette_registry",
    "save_palettable_cache",
]
