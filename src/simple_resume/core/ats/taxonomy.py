"""Skills taxonomy API integration with offline-first fallback.

This module provides optional integration with external skills taxonomy APIs
(LinkedIn Skills API, O*NET) while maintaining offline-first behavior.

Features:
- Offline-first: Hardcoded list remains default
- Optional opt-in: API fetch only when explicitly enabled
- Local caching: Cached taxonomy data minimizes API calls
- Graceful degradation: Falls back to hardcoded list on failure

See GitHub Issue #59 for design rationale.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache directory for taxonomy data
TAXONOMY_CACHE_DIR = Path.home() / ".cache" / "simple-resume" / "taxonomy"
TAXONOMY_CACHE_TTL = 7 * 24 * 60 * 60  # 7 days in seconds


# Hardcoded fallback skills list (current implementation)
HARDCODED_SKILLS = [
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
]


@dataclass
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


@dataclass
class TaxonomyCache:
    """Local file system cache for taxonomy data.

    Attributes:
        cache_dir: Directory for cache files
        ttl: Time-to-live for cached data

    """

    cache_dir: Path = field(default_factory=lambda: TAXONOMY_CACHE_DIR)
    ttl: int = TAXONOMY_CACHE_TTL

    def _get_cache_path(self, taxonomy_name: str) -> Path:
        """Get cache file path for a taxonomy."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / f"{taxonomy_name}.json"

    def get(self, taxonomy_name: str) -> list[str] | None:
        """Get cached taxonomy data if valid.

        Args:
            taxonomy_name: Name of the taxonomy (e.g., "onet", "linkedin")

        Returns:
            List of skills if cache is valid, None otherwise

        """
        cache_path = self._get_cache_path(taxonomy_name)

        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            cached_time = data.get("timestamp", 0)

            # Check if cache is still valid
            if time.time() - cached_time > self.ttl:
                logger.debug(f"Cache expired for {taxonomy_name}")
                return None

            skills = data.get("skills", [])
            return list[str](skills) if isinstance(skills, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(f"Failed to read cache for {taxonomy_name}: {exc}")
            return None

    def set(self, taxonomy_name: str, skills: list[str]) -> None:
        """Cache taxonomy data with timestamp.

        Args:
            taxonomy_name: Name of the taxonomy
            skills: List of skills to cache

        """
        cache_path = self._get_cache_path(taxonomy_name)

        data = {
            "timestamp": time.time(),
            "skills": sorted(set(skills)),
        }

        try:
            cache_path.write_text(json.dumps(data, indent=2))
            logger.info(f"Cached {len(skills)} skills from {taxonomy_name}")
        except OSError as exc:
            logger.warning(f"Failed to write cache for {taxonomy_name}: {exc}")


class SkillsTaxonomyFetcher:
    """Fetch skills from external taxonomy APIs with caching.

    Implements offline-first design:
    - Uses hardcoded list as default/fallback
    - Only fetches API when explicitly enabled
    - Caches results locally for performance
    - Falls back on any error

    Attributes:
        config: Taxonomy configuration
        cache: Local cache for taxonomy data

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
        self.config = config or TaxonomyConfig()
        self.cache = cache or TaxonomyCache(ttl=self.config.cache_ttl)

    def get_skills(self, taxonomy: str = "onet") -> list[str]:
        """Get skills from taxonomy with fallback to hardcoded list.

        Args:
            taxonomy: Taxonomy name ("onet", "linkedin", etc.)

        Returns:
            List of skills (from API if enabled and cached, or hardcoded list)

        """
        # If API integration is disabled, use hardcoded list
        if not self.config.enabled:
            logger.debug("Taxonomy API disabled, using hardcoded skills")
            return HARDCODED_SKILLS

        # Try to get from cache first
        cached_skills = self.cache.get(taxonomy)
        if cached_skills is not None:
            logger.debug(f"Using cached skills from {taxonomy}")
            return cached_skills

        # Attempt to fetch from API
        try:
            skills = self._fetch_from_api(taxonomy)
            if skills:
                # Cache the results
                self.cache.set(taxonomy, skills)
                return skills
        except Exception as exc:
            logger.warning(f"Failed to fetch from {taxonomy} API: {exc}")

        # Fallback to hardcoded list on any error
        logger.info(f"Falling back to hardcoded skills for {taxonomy}")
        return HARDCODED_SKILLS

    def _fetch_from_api(self, taxonomy: str) -> list[str]:
        """Fetch skills from taxonomy API.

        Args:
            taxonomy: Taxonomy name

        Returns:
            List of skills from the API

        Raises:
            NotImplementedError: If taxonomy is not yet implemented

        """
        if taxonomy == "onet":
            return self._fetch_onet()
        elif taxonomy == "linkedin":
            return self._fetch_linkedin()
        else:
            raise NotImplementedError(f"Taxonomy '{taxonomy}' not implemented")

    def _fetch_onet(self) -> list[str]:
        """Fetch skills from O*NET API.

        O*NET is the U.S. Department of Labor's occupational database.
        This is a placeholder for future implementation.

        Returns:
            List of skills from O*NET

        Note:
            This is a stub for future implementation. Actual implementation
            would query O*NET's API or download their data files.

        """
        # TODO: Implement O*NET API integration
        # O*NET provides downloadable data files at:
        # https://www.onetcenter.org/dictionary_files.html
        logger.info("O*NET integration not yet implemented, using fallback")
        return []

    def _fetch_linkedin(self) -> list[str]:
        """Fetch skills from LinkedIn Skills API.

        This is a placeholder for future implementation.
        LinkedIn's Skills API requires OAuth authentication.

        Returns:
            List of skills from LinkedIn

        Note:
            This is a stub for future implementation. Actual implementation
            would require LinkedIn API credentials and OAuth flow.

        """
        # TODO: Implement LinkedIn Skills API integration
        logger.info(
            "LinkedIn Skills API integration not yet implemented, using fallback"
        )
        return []


def get_enhanced_skills(
    use_taxonomy: bool = False,
    taxonomy: str = "onet",
) -> list[str]:
    """Get skills with optional taxonomy API integration.

    This is the main entry point for taxonomy-enhanced skill extraction.

    Args:
        use_taxonomy: Enable taxonomy API integration (default: False)
        taxonomy: Taxonomy name to use ("onet", "linkedin")

    Returns:
        List of skills (from taxonomy API if enabled, or hardcoded list)

    Example:
        >>> # Default: offline-first with hardcoded skills
        >>> skills = get_enhanced_skills()
        >>> len(skills) > 50
        True

        >>> # Enable taxonomy API (requires network, cache, or valid API)
        >>> skills = get_enhanced_skills(use_taxonomy=True, taxonomy="onet")
        >>> len(skills) > 50
        True

    """
    config = TaxonomyConfig(enabled=use_taxonomy)
    fetcher = SkillsTaxonomyFetcher(config)
    return fetcher.get_skills(taxonomy)


# Backwards compatibility: expose hardcoded skills directly
DEFAULT_SKILLS_LIST = HARDCODED_SKILLS

__all__ = [
    "TaxonomyConfig",
    "TaxonomyCache",
    "SkillsTaxonomyFetcher",
    "get_enhanced_skills",
    "DEFAULT_SKILLS_LIST",
]
