"""File system cache implementation for taxonomy data.

This module provides the concrete TaxonomyLocalCache implementation
that performs file I/O, following the functional core / imperative shell pattern.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from simple_resume.core.ats.taxonomy import TAXONOMY_CACHE_TTL

logger = logging.getLogger(__name__)

# Cache directory for taxonomy data
TAXONOMY_CACHE_DIR = Path.home() / ".cache" / "simple-resume" / "taxonomy"


@dataclass
class TaxonomyLocalCache:
    """Local file system cache for taxonomy data.

    This is the shell layer implementation of the TaxonomyCache protocol
    defined in core.ats.taxonomy.
    """

    cache_dir: Path = field(default_factory=lambda: TAXONOMY_CACHE_DIR)
    ttl: int = TAXONOMY_CACHE_TTL

    def __post_init__(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, taxonomy_name: str) -> Path:
        """Get cache file path for a taxonomy."""
        return self.cache_dir / f"{taxonomy_name}.json"

    def get(self, taxonomy_name: str) -> list[str] | None:
        """Get cached taxonomy data if valid."""
        cache_path = self._get_cache_path(taxonomy_name)

        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            cached_time = data.get("timestamp", 0)

            if time.time() - cached_time > self.ttl:
                logger.debug("Cache expired for %s", taxonomy_name)
                return None

            skills = data.get("skills", [])
            return list(skills) if isinstance(skills, list) else []
        except json.JSONDecodeError as exc:
            logger.warning("Corrupted cache detected for %s: %s", taxonomy_name, exc)
            return None
        except OSError as exc:
            logger.warning("Failed to read cache for %s: %s", taxonomy_name, exc)
            return None

    def set(self, taxonomy_name: str, skills: list[str]) -> None:
        """Cache taxonomy data with timestamp."""
        cache_path = self._get_cache_path(taxonomy_name)

        data = {
            "timestamp": time.time(),
            "skills": sorted(set(skills)),
        }

        try:
            cache_path.write_text(json.dumps(data, indent=2))
            logger.info("Cached %d skills from %s", len(skills), taxonomy_name)
        except OSError as exc:
            logger.error("Failed to write cache for %s: %s", taxonomy_name, exc)


__all__ = ["TaxonomyLocalCache", "TAXONOMY_CACHE_DIR"]
