"""Unit tests for skills taxonomy API integration.

Tests the offline-first taxonomy system with caching and graceful degradation.
Follows TDD: RED (failing test) -> GREEN (implementation) -> REFACTOR.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.core.ats.taxonomy import (
    DEFAULT_SKILLS_LIST,
    SkillsTaxonomyFetcher,
    TaxonomyConfig,
    get_enhanced_skills,
)
from simple_resume.shell.taxonomy_cache import TaxonomyLocalCache as TaxonomyCache


class TestTaxonomyConfig:
    """Tests for TaxonomyConfig dataclass."""

    def test_default_values(self):
        """Test TaxonomyConfig has correct defaults."""
        config = TaxonomyConfig()
        assert config.enabled is False  # Offline-first by default
        assert config.cache_ttl == 7 * 24 * 60 * 60
        assert config.api_timeout == 10
        assert config.max_retries == 3

    def test_enabled_can_be_set(self):
        """Test enabled flag can be configured."""
        config = TaxonomyConfig(enabled=True)
        assert config.enabled is True


class TestTaxonomyCache:
    """Tests for TaxonomyCache file system caching."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "taxonomy"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def test_cache_returns_none_for_missing_file(self, temp_cache_dir: Path):
        """Test cache returns None when file doesn't exist."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_stores_and_retrieves_data(self, temp_cache_dir: Path):
        """Test cache can store and retrieve taxonomy data."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)

        skills = ["Python", "JavaScript", "Docker"]
        cache.set("test_taxonomy", skills)

        retrieved = cache.get("test_taxonomy")
        assert sorted(retrieved) == sorted(skills)

    def test_cache_returns_none_when_expired(self, temp_cache_dir: Path):
        """Test cache returns None when data is past TTL."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=-1)  # Expired

        skills = ["Python", "JavaScript"]
        cache.set("test_taxonomy", skills)

        retrieved = cache.get("test_taxonomy")
        assert retrieved is None  # Expired cache returns None

    def test_cache_includes_timestamp(self, temp_cache_dir: Path):
        """Test cached data includes timestamp."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)
        cache.set("test_taxonomy", ["skill1", "skill2"])

        cache_path = temp_cache_dir / "test_taxonomy.json"
        data = json.loads(cache_path.read_text())

        assert "timestamp" in data
        assert "skills" in data
        assert isinstance(data["timestamp"], (int, float))


class TestSkillsTaxonomyFetcher:
    """Tests for SkillsTaxonomyFetcher."""

    def test_offline_first_returns_hardcoded_skills_by_default(self):
        """Test fetcher returns hardcoded skills when API disabled."""
        config = TaxonomyConfig(enabled=False)
        fetcher = SkillsTaxonomyFetcher(config)

        skills = fetcher.get_skills("onet")
        assert skills == DEFAULT_SKILLS_LIST

    def test_enabled_api_returns_hardcoded_on_cache_miss(self, tmp_path: Path):
        """Test fetcher falls back to hardcoded when API fetch fails."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Cache miss + API not implemented = fallback
        skills = fetcher.get_skills("onet")
        assert skills == DEFAULT_SKILLS_LIST

    def test_uses_cached_data_when_available(self, tmp_path: Path):
        """Test fetcher uses cached data when available."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)

        # Pre-seed cache
        cached_skills = ["CachedSkill1", "CachedSkill2"]
        cache.set("test_taxonomy", cached_skills)

        fetcher = SkillsTaxonomyFetcher(config, cache=cache)
        skills = fetcher.get_skills("test_taxonomy")

        assert skills == cached_skills

    def test_unimplemented_taxonomy_falls_back_gracefully(self, tmp_path: Path):
        """Test unimplemented taxonomy falls back to hardcoded list."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # "unimplemented" taxonomy doesn't exist
        skills = fetcher.get_skills("unimplemented")
        assert skills == DEFAULT_SKILLS_LIST  # Graceful fallback


class TestGetEnhancedSkills:
    """Tests for the main get_enhanced_skills function."""

    def test_default_returns_hardcoded_skills(self):
        """Test default behavior returns hardcoded skills (offline-first)."""
        skills = get_enhanced_skills()
        assert skills == DEFAULT_SKILLS_LIST
        assert len(skills) > 50  # Should have many skills

    def test_disabled_taxonomy_returns_hardcoded(self):
        """Test explicit disable returns hardcoded skills."""
        skills = get_enhanced_skills(use_taxonomy=False)
        assert skills == DEFAULT_SKILLS_LIST

    @patch("simple_resume.core.ats.taxonomy.SkillsTaxonomyFetcher")
    def test_enabled_taxonomy_uses_fetcher(self, mock_fetcher_class: Mock):
        """Test enabled taxonomy uses SkillsTaxonomyFetcher."""
        mock_instance = Mock()
        mock_instance.get_skills.return_value = ["API", "Skills"]
        mock_fetcher_class.return_value = mock_instance

        skills = get_enhanced_skills(use_taxonomy=True, taxonomy="onet")

        assert skills == ["API", "Skills"]
        mock_instance.get_skills.assert_called_once_with("onet")

    def test_default_skills_list_is_exported(self):
        """Test DEFAULT_SKILLS_LIST is accessible for backwards compatibility."""
        assert DEFAULT_SKILLS_LIST
        assert len(DEFAULT_SKILLS_LIST) > 50
