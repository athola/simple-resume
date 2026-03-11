"""Unit tests for skills taxonomy API integration and data bundles (#81, #82).

Tests the offline-first taxonomy system with caching, graceful degradation,
and bundled O*NET / LinkedIn skills data.
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
    HARDCODED_SKILLS,
    NullTaxonomyCache,
    SkillsTaxonomyFetcher,
    TaxonomyConfig,
    get_enhanced_skills,
)
from simple_resume.core.ats.taxonomy_data.linkedin_skills import LINKEDIN_SKILLS
from simple_resume.core.ats.taxonomy_data.onet_skills import ONET_SKILLS
from simple_resume.shell.ats.taxonomy_fetcher import (
    LinkedInApiFetcher,
    OnetApiFetcher,
)
from simple_resume.shell.taxonomy_cache import TaxonomyLocalCache as TaxonomyCache
from tests.bdd import Scenario


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

    def test_offline_first_returns_merged_skills_by_default(self):
        """Test fetcher returns merged skills when API disabled."""
        config = TaxonomyConfig(enabled=False)
        fetcher = SkillsTaxonomyFetcher(config)

        skills = fetcher.get_skills("onet")
        # With bundles merged in, result is a superset of hardcoded skills
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)
        skills_lower = {s.lower() for s in skills}
        for s in DEFAULT_SKILLS_LIST[:5]:
            assert s.lower() in skills_lower

    def test_enabled_api_falls_back_on_cache_miss_not_implemented(self, tmp_path: Path):
        """Test fetcher falls back when API stub raises."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Cache miss + API not implemented = graceful fallback to merged bundles
        skills = fetcher.get_skills("onet")
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)
        skills_lower = {s.lower() for s in skills}
        for s in DEFAULT_SKILLS_LIST[:5]:
            assert s.lower() in skills_lower

    def test_uses_cached_data_when_available(self, tmp_path: Path):
        """Test fetcher includes cached data in merged results."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)

        # Pre-seed cache
        cached_skills = ["CachedSkill1", "CachedSkill2"]
        cache.set("test_taxonomy", cached_skills)

        fetcher = SkillsTaxonomyFetcher(config, cache=cache)
        skills = fetcher.get_skills("test_taxonomy")

        # Merged pipeline: hardcoded + bundles + cached (deduplicated)
        skills_lower = {s.lower() for s in skills}
        for s in cached_skills:
            assert s.lower() in skills_lower
        assert len(skills) > len(cached_skills)

    def test_unknown_taxonomy_falls_back_to_merged_skills(self, tmp_path: Path):
        """Test unknown taxonomy string falls back to merged hardcoded + bundle skills.

        With TaxonomySource enum, an invalid string raises ValueError during
        enum conversion in _fetch_from_api. Since get_skills catches ValueError,
        it gracefully uses hardcoded + bundle skills.
        """
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # "unknown" is not a valid TaxonomySource, triggers ValueError fallback
        skills = fetcher.get_skills("unknown")
        # Result includes hardcoded + bundles (superset of hardcoded alone)
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)
        skills_lower = {s.lower() for s in skills}
        for s in DEFAULT_SKILLS_LIST[:5]:
            assert s.lower() in skills_lower


class TestGetEnhancedSkills:
    """Tests for the main get_enhanced_skills function."""

    def test_default_returns_merged_skills(self):
        """Test default returns merged hardcoded + bundle skills."""
        skills = get_enhanced_skills()
        assert len(skills) > 50  # Should have many skills
        # Bundles are always merged in, result is superset of hardcoded
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)

    def test_disabled_taxonomy_returns_merged_skills(self):
        """Test explicit disable still returns hardcoded + bundle skills."""
        skills = get_enhanced_skills(use_taxonomy=False)
        # Bundles always included regardless of use_taxonomy flag
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)

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

        # Should still work, using hardcoded + bundle skills
        skills = fetcher.get_skills("onet")
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)
        skills_lower = {s.lower() for s in skills}
        for s in DEFAULT_SKILLS_LIST[:5]:
            assert s.lower() in skills_lower


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


class TestTaxonomyApiStubs:
    """Tests for taxonomy API stubs (all backends unimplemented).

    The live API stubs raise NotImplementedError, but get_skills()
    catches it and falls back to merged bundle data gracefully.
    """

    def test_onet_api_fallback_on_not_implemented(self, tmp_path: Path):
        """Test O*NET API stub failure falls back to merged bundles."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Should NOT raise — graceful fallback to merged bundles
        skills = fetcher.get_skills("onet")
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)

    def test_linkedin_api_fallback_on_not_implemented(self, tmp_path: Path):
        """Test LinkedIn API stub failure falls back to merged bundles."""
        config = TaxonomyConfig(enabled=True)
        cache = TaxonomyCache(cache_dir=tmp_path / "taxonomy", ttl=1000)
        fetcher = SkillsTaxonomyFetcher(config, cache=cache)

        # Should NOT raise — graceful fallback to merged bundles
        skills = fetcher.get_skills("linkedin")
        assert len(skills) >= len(DEFAULT_SKILLS_LIST)


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
            # First call should fetch, cache, and merge with bundles
            result = fetcher.get_skills("mock_taxonomy")
            # Result includes bundles + mock_skills (deduplicated)
            result_lower = {s.lower() for s in result}
            for s in mock_skills:
                assert s.lower() in result_lower

        # Verify API results were cached (only the API portion)
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
            # Result includes bundles + cached skill (deduplicated)
            result_lower = {s.lower() for s in result}
            assert "cachedskill" in result_lower


class TestOnetBundle:
    """O*NET skills bundle loads correctly."""

    def test_onet_skills_is_nonempty_list(self, story: Scenario) -> None:
        story.given("the O*NET skills bundle module")
        story.when("accessing the skills list")
        story.then("it contains a substantial number of skills")
        assert isinstance(ONET_SKILLS, (list, tuple))
        assert len(ONET_SKILLS) >= 200

    def test_onet_skills_contains_common_tech(self, story: Scenario) -> None:
        story.given("the O*NET skills bundle")
        story.when("checking for common technology skills")
        skills_lower = {s.lower() for s in ONET_SKILLS}

        story.then("common skills are present")
        assert "python" in skills_lower
        assert "sql" in skills_lower
        assert "project management" in skills_lower


class TestLinkedInBundle:
    """LinkedIn skills bundle loads correctly."""

    def test_linkedin_skills_is_nonempty_list(self, story: Scenario) -> None:
        story.given("the LinkedIn skills bundle module")
        story.when("accessing the skills list")
        story.then("it contains a substantial number of skills")
        assert isinstance(LINKEDIN_SKILLS, (list, tuple))
        assert len(LINKEDIN_SKILLS) >= 200

    def test_linkedin_skills_contains_soft_skills(self, story: Scenario) -> None:
        story.given("the LinkedIn skills bundle")
        story.when("checking for soft skills common on LinkedIn")
        skills_lower = {s.lower() for s in LINKEDIN_SKILLS}

        story.then("professional soft skills are present")
        assert "leadership" in skills_lower
        assert "communication" in skills_lower


class TestMergedSkillsPipeline:
    """get_enhanced_skills merges hardcoded + bundle skills."""

    def test_enhanced_skills_includes_hardcoded(self, story: Scenario) -> None:
        story.given("default taxonomy configuration")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()
        skills_lower = {s.lower() for s in skills}

        story.then("hardcoded skills are included")
        for skill in HARDCODED_SKILLS[:5]:
            assert skill.lower() in skills_lower

    def test_enhanced_skills_includes_bundles(self, story: Scenario) -> None:
        story.given("default taxonomy configuration")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()

        story.then("result is larger than hardcoded list alone")
        assert len(skills) > len(HARDCODED_SKILLS)

    def test_enhanced_skills_deduplicates(self, story: Scenario) -> None:
        story.given("skills from multiple sources with overlaps")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()
        skills_lower = [s.lower() for s in skills]

        story.then("no duplicates exist (case-insensitive)")
        assert len(skills_lower) == len(set(skills_lower))

    def test_fetcher_get_skills_without_api(self, story: Scenario) -> None:
        story.given("a fetcher with API disabled (default)")
        fetcher = SkillsTaxonomyFetcher()

        story.when("getting skills")
        skills = fetcher.get_skills()

        story.then("returns merged hardcoded + bundle skills")
        assert len(skills) > len(HARDCODED_SKILLS)


class TestApiFetcherStubs:
    """Shell-layer API fetcher stubs are importable."""

    def test_onet_fetcher_exists(self, story: Scenario) -> None:
        story.given("the shell-layer taxonomy fetcher module")
        story.when("instantiating the O*NET fetcher")
        fetcher = OnetApiFetcher()

        story.then("it has a fetch method")
        assert hasattr(fetcher, "fetch")

    def test_linkedin_fetcher_exists(self, story: Scenario) -> None:
        story.given("the shell-layer taxonomy fetcher module")
        story.when("instantiating the LinkedIn fetcher")
        fetcher = LinkedInApiFetcher()

        story.then("it has a fetch method")
        assert hasattr(fetcher, "fetch")

    def test_onet_fetcher_requires_credentials(self, story: Scenario) -> None:
        story.given("an O*NET fetcher without credentials")
        fetcher = OnetApiFetcher()

        story.when("attempting to fetch without env vars")
        with pytest.raises(NotImplementedError):
            fetcher.fetch()

        story.then("NotImplementedError is raised with guidance")
