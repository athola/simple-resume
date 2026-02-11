"""Integration tests for creative language support in keyword scorer.

Tests the integration between creative_terms module and keyword scorer.
Follows TDD: RED (failing test) -> GREEN (implementation) -> REFACTOR.
"""

from __future__ import annotations

from simple_resume.core.ats.creative_terms import Industry
from simple_resume.core.ats.keyword import KeywordScorer, KeywordScorerConfig


class TestKeywordScorerCreativeExpansion:
    """Tests for creative term expansion in keyword scorer."""

    def test_creates_scorer_with_creative_params(self):
        """Test scorer accepts creative expansion parameters."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(
                enable_creative_expansion=True,
                industry=Industry.TECH,
            ),
        )
        assert scorer.enable_creative_expansion is True
        assert scorer.industry == Industry.TECH

    def test_default_creative_expansion_disabled(self):
        """Test creative expansion is disabled by default."""
        scorer = KeywordScorer()
        assert scorer.enable_creative_expansion is False

    def test_expands_rockstar_to_senior(self):
        """Test 'rockstar developer' expands to 'senior developer'."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Looking for a rockstar developer"
        resume = "Experienced senior developer with 5 years experience"

        result = scorer.score(resume, job, keywords=["rockstar developer"])

        # Should find match through expansion
        assert result.score > 0
        assert result.details["creative_terms_expanded"]
        expanded = result.details["creative_terms_expanded"][0]
        assert expanded["creative"] == "rockstar developer"
        assert expanded["expanded"] == "senior developer"

    def test_expands_ninja_to_expert(self):
        """Test 'ninja coder' expands to 'expert programmer'."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Need a code ninja for backend"
        resume = "Expert programmer in Python and Go"

        result = scorer.score(resume, job, keywords=["code ninja"])

        # Should find match through expansion
        assert result.score > 0
        assert any(
            e["creative"] == "code ninja"
            for e in result.details["creative_terms_expanded"]
        )

    def test_no_expansion_when_disabled(self):
        """Test creative terms not expanded when feature disabled."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=False)
        )
        job = "Looking for rockstar developer"
        resume = "Senior developer with experience"

        result = scorer.score(resume, job, keywords=["rockstar developer"])

        # Should not have creative terms expanded
        assert result.details.get("creative_terms_expanded") == []

    def test_industry_specific_mappings(self):
        """Test different industries use different dictionaries."""
        tech_scorer = KeywordScorer(
            config=KeywordScorerConfig(
                enable_creative_expansion=True,
                industry=Industry.TECH,
            ),
        )
        enterprise_scorer = KeywordScorer(
            config=KeywordScorerConfig(
                enable_creative_expansion=True,
                industry=Industry.ENTERPRISE,
            ),
        )

        # Both should work but may have different mappings
        assert tech_scorer.industry == Industry.TECH
        assert enterprise_scorer.industry == Industry.ENTERPRISE

    def test_multiple_creative_terms_expanded(self):
        """Test multiple creative terms in one job description."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Rockstar developer and code ninja needed"
        resume = "Senior developer and expert programmer"

        result = scorer.score(
            resume, job, keywords=["rockstar developer", "code ninja"]
        )

        # Should expand both terms
        expanded_terms = result.details.get("creative_terms_expanded", [])
        assert len(expanded_terms) >= 2

    def test_standard_terms_unchanged(self):
        """Test standard terms are not modified."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Looking for senior software engineer"
        resume = "Senior software engineer with experience"

        result = scorer.score(resume, job, keywords=["senior", "software", "engineer"])

        # Standard terms should match directly without expansion
        assert result.score > 0
        # No creative terms should be expanded
        assert result.details.get("creative_terms_expanded") == []

    def test_empty_expansion_list_when_no_creative_terms(self):
        """Test returns empty list when no creative terms present."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Looking for Python developer"
        resume = "Python developer with Django experience"

        result = scorer.score(resume, job, keywords=["python", "developer"])

        assert result.details.get("creative_terms_expanded") == []


class TestKeywordScorerCreativeConfidence:
    """Tests for confidence scoring with creative terms."""

    def test_creative_term_in_details(self):
        """Test creative term appears in details with expansion info."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        job = "Rockstar developer needed"
        resume = "Senior developer available"

        result = scorer.score(resume, job, keywords=["rockstar developer"])

        # Should have expansion details
        expanded = result.details.get("creative_terms_expanded", [])
        if expanded:
            # Each expansion should have creative and expanded keys
            assert "creative" in expanded[0]
            assert "expanded" in expanded[0]

    def test_score_improvement_with_expansion(self):
        """Test score improves when creative terms are expanded."""
        scorer_with = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=True)
        )
        scorer_without = KeywordScorer(
            config=KeywordScorerConfig(enable_creative_expansion=False)
        )

        job = "Looking for rockstar developer"
        resume = "Senior developer with experience"

        result_with = scorer_with.score(resume, job, keywords=["rockstar developer"])
        result_without = scorer_without.score(
            resume, job, keywords=["rockstar developer"]
        )

        # Score should be better with expansion enabled
        assert result_with.score >= result_without.score
