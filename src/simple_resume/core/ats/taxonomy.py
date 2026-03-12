"""Skills taxonomy API integration with offline-first fallback.

This module provides optional integration with external skills taxonomy APIs
(LinkedIn Skills API, O*NET) while maintaining offline-first behavior.

Features:
- Offline-first: Hardcoded list remains default
- Optional opt-in: API fetch only when explicitly enabled
- Local caching: Cached taxonomy data minimizes API calls
- Graceful degradation: Falls back to hardcoded list on failure

See GitHub Issue #59 for design rationale.

Architecture Note:
The TaxonomyCache Protocol defines the interface for caching taxonomy data.
The concrete implementation (TaxonomyLocalCache) lives in shell layer to
maintain core/shell separation. See ADR002 (Functional Core / Imperative Shell).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from simple_resume.core.ats.taxonomy_data import LINKEDIN_SKILLS, ONET_SKILLS

logger = logging.getLogger(__name__)


class TaxonomySource(str, Enum):
    """Supported taxonomy API sources."""

    ONET = "onet"
    LINKEDIN = "linkedin"


# Default cache TTL
TAXONOMY_CACHE_TTL = 7 * 24 * 60 * 60  # 7 days in seconds


# Hardcoded fallback skills list (current implementation)
HARDCODED_SKILLS: tuple[str, ...] = (
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C++",
    "C#",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "Swift",
    "Kotlin",
    "SQL",
    "NoSQL",
    "MongoDB",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "Elasticsearch",
    "DynamoDB",
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Jenkins",
    "Git",
    "GitHub",
    "GitLab",
    "Linux",
    "Unix",
    "Bash",
    "Shell",
    "PowerShell",
    "TensorFlow",
    "PyTorch",
    "Keras",
    "scikit-learn",
    "pandas",
    "numpy",
    "HTML",
    "CSS",
    "SASS",
    "REST",
    "GraphQL",
    "gRPC",
    "React",
    "Vue",
    "Angular",
    "Svelte",
    "Next.js",
    "Nuxt.js",
    "Django",
    "Flask",
    "FastAPI",
    "Spring",
    "Express",
)


@dataclass(frozen=True)
class TaxonomyConfig:
    """Configuration for taxonomy API integration.

    Attributes:
        enabled: Whether to use taxonomy API (default: False for offline-first)
        cache_ttl: Time-to-live for cached data in seconds
        api_timeout: Timeout for API requests in seconds
        max_retries: Maximum retry attempts for API requests

    """

    enabled: bool = False
    cache_ttl: int = TAXONOMY_CACHE_TTL
    api_timeout: int = 10
    max_retries: int = 3

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.cache_ttl <= 0:
            raise ValueError(f"cache_ttl must be > 0, got {self.cache_ttl}")
        if self.api_timeout <= 0:
            raise ValueError(f"api_timeout must be > 0, got {self.api_timeout}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")


class TaxonomyCache(Protocol):
    """Protocol for taxonomy data caching.

    This defines the interface for caching taxonomy data. Concrete implementations
    (e.g., TaxonomyLocalCache in shell layer) handle actual file I/O.

    This separation maintains the functional core / imperative shell architecture.
    See ADR002 (Functional Core / Imperative Shell) for design rationale.
    """

    def get(self, taxonomy_name: str) -> list[str] | None:
        """Get cached taxonomy data if valid.

        Args:
            taxonomy_name: Name of the taxonomy (e.g., "onet", "linkedin")

        Returns:
            List of skills if cache is valid, None otherwise

        """
        ...

    def set(self, taxonomy_name: str, skills: list[str]) -> None:
        """Cache taxonomy data with timestamp.

        Args:
            taxonomy_name: Name of the taxonomy
            skills: List of skills to cache

        """
        ...


class NullTaxonomyCache:
    """No-op cache implementation for when caching is disabled.

    This is a pure in-memory implementation with no file I/O,
    suitable for use in the core layer.
    """

    def get(self, _taxonomy_name: str) -> list[str] | None:
        """Return None (cache miss) for all lookups."""
        return None

    def set(self, _taxonomy_name: str, _skills: list[str]) -> None:
        """No-op: does not store anything."""
        pass


class SkillsTaxonomyFetcher:
    """Fetch skills from external taxonomy APIs with caching.

    Implements offline-first design:
    - Uses hardcoded list as default/fallback
    - Only fetches API when explicitly enabled
    - Caches results locally for performance
    - Falls back on any error

    """

    def __init__(
        self,
        config: TaxonomyConfig | None = None,
        cache: TaxonomyCache | None = None,
    ) -> None:
        """Initialize the fetcher.

        Args:
            config: Taxonomy configuration (uses defaults if None)
            cache: Optional cache instance (uses default if None)

        """
        self._config = config or TaxonomyConfig()
        self._cache = cache or NullTaxonomyCache()

    @staticmethod
    def _load_onet_bundle() -> list[str]:
        """Load curated O*NET skills bundle (no I/O, always succeeds)."""
        return list(ONET_SKILLS)

    @staticmethod
    def _load_linkedin_bundle() -> list[str]:
        """Load curated LinkedIn skills bundle (no I/O, always succeeds)."""
        return list(LINKEDIN_SKILLS)

    def get_skills(
        self, taxonomy: str | TaxonomySource = TaxonomySource.ONET
    ) -> list[str]:
        """Get merged skills from hardcoded list, bundles, and optional API.

        Returns deduplicated, lowercase-normalized list of skills from:
        1. Hardcoded skills (always included)
        2. O*NET bundle (always included)
        3. LinkedIn bundle (always included)
        4. Live API results (only if config.enabled and API available)
        """
        all_skills: list[str] = list(HARDCODED_SKILLS)
        all_skills.extend(self._load_onet_bundle())
        all_skills.extend(self._load_linkedin_bundle())

        # Optionally fetch from live API
        if self._config.enabled:
            cached_skills = self._cache.get(taxonomy)
            if cached_skills is not None:
                logger.debug("Using cached skills from %s", taxonomy)
                all_skills.extend(cached_skills)
            else:
                try:
                    api_skills = self._fetch_from_api(taxonomy)
                    if api_skills:
                        self._cache.set(taxonomy, api_skills)
                        all_skills.extend(api_skills)
                except (
                    OSError,
                    ConnectionError,
                    TimeoutError,
                    ValueError,
                    NotImplementedError,
                ) as exc:
                    logger.warning("Failed to fetch from %s API: %s", taxonomy, exc)

        # Deduplicate (case-insensitive) preserving first occurrence
        seen: set[str] = set()
        unique: list[str] = []
        for skill in all_skills:
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                unique.append(skill)
        return unique

    def _fetch_from_api(self, taxonomy: str | TaxonomySource) -> list[str]:
        """Fetch skills from a taxonomy API.

        This is a stub for future implementation. When taxonomy backends
        are added, dispatch on ``TaxonomySource`` here.

        Args:
            taxonomy: Taxonomy source name or enum value

        Returns:
            List of skills from the API

        Raises:
            NotImplementedError: Always — no backends implemented yet

        """
        source = TaxonomySource(taxonomy) if isinstance(taxonomy, str) else taxonomy
        raise NotImplementedError(
            f"Taxonomy '{source.value}' API integration not yet implemented"
        )


def get_enhanced_skills(
    use_taxonomy: bool = False,
    taxonomy: str | TaxonomySource = TaxonomySource.ONET,
) -> list[str]:
    """Get skills with bundled taxonomy data and optional API integration.

    Always merges hardcoded + O*NET + LinkedIn bundles. When use_taxonomy=True,
    also attempts live API fetch with caching.
    """
    config = TaxonomyConfig(enabled=use_taxonomy)
    fetcher = SkillsTaxonomyFetcher(config)
    return fetcher.get_skills(taxonomy)


# Backwards compatibility: expose hardcoded skills directly
DEFAULT_SKILLS_LIST = HARDCODED_SKILLS

__all__ = [
    "TaxonomyConfig",
    "TaxonomyCache",
    "TaxonomySource",
    "SkillsTaxonomyFetcher",
    "get_enhanced_skills",
    "DEFAULT_SKILLS_LIST",
]
