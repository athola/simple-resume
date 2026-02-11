"""Unit tests for skills taxonomy API integration.

Tests the offline-first taxonomy system with caching and graceful degradation.
Follows TDD: RED (failing test) -> GREEN (implementation) -> REFACTOR.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.core.ats.taxonomy import (
    DEFAULT_SKILLS_LIST,
    NullTaxonomyCache,
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
        assert skills == list(DEFAULT_SKILLS_LIST)

    def test_enabled_api_raises_on_cache_miss_not_implemented(self, tmp_path: Path):
        """Test fetcher raises NotImplementedError when API stub is called."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Cache miss + API not implemented = NotImplementedError propagates
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            fetcher.get_skills("onet")

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

    def test_unknown_taxonomy_falls_back_to_hardcoded(self, tmp_path: Path):
        """Test unknown taxonomy string falls back to hardcoded skills.

        With TaxonomySource enum, an invalid string raises ValueError during
        enum conversion in _fetch_from_api. Since get_skills catches ValueError,
        it gracefully falls back to the hardcoded skills list.
        """
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # "unknown" is not a valid TaxonomySource, triggers ValueError fallback
        skills = fetcher.get_skills("unknown")
        assert skills == list(DEFAULT_SKILLS_LIST)


class TestGetEnhancedSkills:
    """Tests for the main get_enhanced_skills function."""

    def test_default_returns_hardcoded_skills(self):
        """Test default behavior returns hardcoded skills (offline-first)."""
        skills = get_enhanced_skills()
        assert skills == list(DEFAULT_SKILLS_LIST)
        assert len(skills) > 50  # Should have many skills

    def test_disabled_taxonomy_returns_hardcoded(self):
        """Test explicit disable returns hardcoded skills."""
        skills = get_enhanced_skills(use_taxonomy=False)
        assert skills == list(DEFAULT_SKILLS_LIST)

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


class TestNullTaxonomyCache:
    """Tests for NullTaxonomyCache no-op implementation."""

    def test_get_always_returns_none(self):
        """Test NullTaxonomyCache.get() always returns None (cache miss)."""
        cache = NullTaxonomyCache()

        assert cache.get("onet") is None
        assert cache.get("linkedin") is None
        assert cache.get("any_taxonomy") is None

    def test_set_is_noop(self):
        """Test NullTaxonomyCache.set() does nothing (no-op)."""
        cache = NullTaxonomyCache()

        # Should not raise, should have no effect
        cache.set("test", ["Python", "JavaScript"])

        # Subsequent get still returns None
        assert cache.get("test") is None

    def test_used_by_fetcher_when_no_cache_provided(self):
        """Test fetcher uses NullTaxonomyCache by default."""
        config = TaxonomyConfig(enabled=False)
        fetcher = SkillsTaxonomyFetcher(config)

        # Should still work, using hardcoded skills
        skills = fetcher.get_skills("onet")
        assert skills == list(DEFAULT_SKILLS_LIST)


class TestTaxonomyCacheErrorHandling:
    """Tests for TaxonomyCache error handling."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "taxonomy"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def test_handles_corrupted_json_gracefully(self, temp_cache_dir: Path):
        """Test cache handles corrupted JSON files gracefully."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)

        # Write corrupted JSON to cache file
        cache_path = temp_cache_dir / "corrupted.json"
        cache_path.write_text("{invalid json content")

        # Should return None (cache miss), not raise
        result = cache.get("corrupted")
        assert result is None

    def test_handles_write_failure_gracefully(self, temp_cache_dir: Path, monkeypatch):
        """Test cache handles write failures gracefully."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)

        # Patch write_text to raise OSError for taxonomy files
        original_write_text = Path.write_text

        def patched_write_text(self, content, **kwargs):
            if "taxonomy" in str(self):
                raise OSError("Simulated write failure")
            return original_write_text(self, content, **kwargs)

        monkeypatch.setattr(Path, "write_text", patched_write_text)

        # Should not raise, just log warning
        cache.set("test_write_fail", ["Python"])

        # Verify nothing was cached (can't write)
        # Reset monkeypatch to read properly
        monkeypatch.undo()
        result = cache.get("test_write_fail")
        assert result is None

    def test_handles_non_list_skills_data(self, temp_cache_dir: Path):
        """Test cache handles invalid skills data type gracefully."""
        cache = TaxonomyCache(cache_dir=temp_cache_dir, ttl=1000)

        # Write JSON with invalid skills type
        cache_path = temp_cache_dir / "invalid_type.json"
        cache_path.write_text(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "skills": "not a list",  # Should be list
                }
            )
        )

        # Should return empty list (defensive coding)
        result = cache.get("invalid_type")
        assert result == []


class TestLinkedInTaxonomy:
    """Tests for LinkedIn taxonomy stub."""

    def test_linkedin_taxonomy_raises_not_implemented(self, tmp_path: Path):
        """Test LinkedIn taxonomy raises NotImplementedError."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # LinkedIn API not implemented - propagates as NotImplementedError
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            fetcher.get_skills("linkedin")

    def test_linkedin_fetch_raises_not_implemented(self):
        """Test _fetch_linkedin raises NotImplementedError (stub)."""
        config = TaxonomyConfig(enabled=True)
        fetcher = SkillsTaxonomyFetcher(config)

        # Directly call private method to verify stub behavior
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            fetcher._fetch_linkedin()


class TestSuccessfulApiFetchCaching:
    """Tests for successful API fetch result caching."""

    def test_successful_fetch_is_cached(self, tmp_path: Path):
        """Test that successful API fetch results are cached."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Mock _fetch_from_api to return skills
        mock_skills = ["MockSkill1", "MockSkill2", "MockSkill3"]

        with patch.object(fetcher, "_fetch_from_api", return_value=mock_skills):
            # First call should fetch and cache
            result = fetcher.get_skills("mock_taxonomy")
            assert sorted(result) == sorted(mock_skills)

        # Verify it was cached
        cached = cache.get("mock_taxonomy")
        assert cached is not None
        assert sorted(cached) == sorted(mock_skills)

    def test_cached_results_used_on_subsequent_calls(self, tmp_path: Path):
        """Test cached results are used instead of re-fetching."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Pre-seed cache
        cache.set("pre_cached", ["CachedSkill"])

        # Mock _fetch_from_api to track calls
        with patch.object(fetcher, "_fetch_from_api") as mock_fetch:
            result = fetcher.get_skills("pre_cached")

            # Should use cached data, not call API
            mock_fetch.assert_not_called()
            assert result == ["CachedSkill"]
