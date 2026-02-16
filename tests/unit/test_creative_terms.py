"""Unit tests for creative language term mappings and detection.

Tests the synonym expansion system for creative/non-standard resume language.
Follows TDD: RED (failing test) -> GREEN (implementation) -> REFACTOR.
"""

from __future__ import annotations

from simple_resume.core.ats.creative_terms import (
    CreativeTerm,
    Industry,
    expand_term,
    get_industry_dictionary,
    is_creative_term,
    normalize_term,
)


class TestNormalizeTerm:
    """Tests for term normalization."""

    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        assert normalize_term("Rockstar Developer") == "rockstar developer"

    def test_normalize_trims_whitespace(self):
        """Test normalization removes extra whitespace."""
        assert normalize_term("  ninja  coder  ") == "ninja coder"

    def test_normalize_empty_string(self):
        """Test normalization handles empty string."""
        assert normalize_term("") == ""

    def test_normalize_single_word(self):
        """Test normalization works with single words."""
        assert normalize_term("GURU") == "guru"


class TestIsCreativeTerm:
    """Tests for creative term detection."""

    def test_detects_known_creative_term(self):
        """Test detection of known creative terms."""
        assert is_creative_term("rockstar developer") is True

    def test_detects_ninja_variant(self):
        """Test detection of ninja-related terms."""
        assert is_creative_term("ninja coder") is True
        assert is_creative_term("code ninja") is True

    def test_returns_false_for_standard_term(self):
        """Test standard terms return False."""
        assert is_creative_term("senior developer") is False
        assert is_creative_term("software engineer") is False

    def test_returns_false_for_empty_string(self):
        """Test empty string returns False."""
        assert is_creative_term("") is False


class TestExpandTerm:
    """Tests for synonym expansion."""

    def test_expand_rockstar_to_senior(self):
        """Test rockstar expands to senior."""
        result = expand_term("rockstar developer")
        assert result == "senior developer"

    def test_expand_ninja_to_expert(self):
        """Test ninja expands to expert."""
        result = expand_term("ninja coder")
        assert result == "expert programmer"

    def test_expand_growth_hacker(self):
        """Test growth hacker expands appropriately."""
        result = expand_term("growth hacker")
        assert "marketing" in result.lower()

    def test_returns_none_for_unknown_term(self):
        """Test unknown terms return None."""
        result = expand_term("unknown creative term")
        assert result is None

    def test_returns_none_for_standard_term(self):
        """Test standard terms return None (no expansion needed)."""
        result = expand_term("senior developer")
        assert result is None


class TestGetIndustryDictionary:
    """Tests for industry-specific dictionaries."""

    def test_tech_industry_includes_terms(self):
        """Test tech industry includes startup-friendly terms."""
        tech_dict = get_industry_dictionary(Industry.TECH)
        assert len(tech_dict) > 0
        assert any("rockstar" in term.creative.lower() for term in tech_dict)

    def test_enterprise_industry_stricter(self):
        """Test enterprise dictionary has stricter mappings."""
        enterprise_dict = get_industry_dictionary(Industry.ENTERPRISE)
        assert len(enterprise_dict) > 0
        # Enterprise should map creative terms to formal equivalents
        assert any("senior" in term.professional.lower() for term in enterprise_dict)

    def test_creative_industry_more_forgiving(self):
        """Test creative industry allows more expression."""
        creative_dict = get_industry_dictionary(Industry.CREATIVE)
        assert len(creative_dict) > 0

    def test_default_industry_is_general(self):
        """Test default industry covers common cases."""
        general_dict = get_industry_dictionary()
        assert len(general_dict) > 0


class TestCreativeTerm:
    """Tests for CreativeTerm dataclass."""

    def test_creative_term_attributes(self):
        """Test CreativeTerm has required attributes."""
        term = CreativeTerm(
            creative="rockstar developer",
            professional="senior developer",
            confidence="low",
        )
        assert term.creative == "rockstar developer"
        assert term.professional == "senior developer"
        assert term.confidence == "low"

    def test_creative_term_with_industry(self):
        """Test CreativeTerm can have industry tag."""
        term = CreativeTerm(
            creative="ninja coder",
            professional="expert programmer",
            confidence="low",
            industry=Industry.TECH,
        )
        assert term.industry == Industry.TECH


class TestConfidenceScoring:
    """Tests for confidence scoring on creative term matches."""

    def test_low_confidence_for_very_creative(self):
        """Test very creative terms get low confidence."""
        term = CreativeTerm(
            creative="rockstar ninja guru",
            professional="senior developer",
            confidence="low",
        )
        assert term.confidence == "low"

    def test_medium_confidence_for_moderate(self):
        """Test moderately creative terms get medium confidence."""
        term = CreativeTerm(
            creative="lead developer",  # Slightly non-standard
            professional="senior developer",
            confidence="medium",
        )
        assert term.confidence == "medium"

    def test_high_confidence_for_near_standard(self):
        """Test near-standard terms get high confidence."""
        term = CreativeTerm(
            creative="software dev",  # Abbreviated but clear
            professional="software developer",
            confidence="high",
        )
        assert term.confidence == "high"
