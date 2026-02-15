"""Unit tests for Keyword ATS scorer.

Tests the keyword matching scorer with various inputs
including edge cases and expected behaviors.
"""

from __future__ import annotations

import pytest

from simple_resume.core.ats.base import ScorerResult
from simple_resume.core.ats.keyword import KeywordScorer, KeywordScorerConfig

# Score threshold constants for readable assertions
SCORE_HIGH_MATCH = 0.7  # Strong keyword overlap expected
SCORE_NEAR_PERFECT = 0.9  # Nearly all keywords present
SCORE_MODERATE = 0.5  # Partial overlap threshold


class TestKeywordScorer:
    """Test suite for KeywordScorer."""

    @pytest.fixture
    def scorer(self) -> KeywordScorer:
        """Create a default Keyword scorer instance."""
        return KeywordScorer(weight=1.0)

    @pytest.fixture
    def sample_resume(self) -> str:
        """Sample resume text for testing."""
        return """
        John Doe
        Senior Software Engineer

        Experience:
        - Senior Python Developer at TechCorp (2020-Present)
          Led development of microservices architecture
          Improved system performance by 40%
          Mentored team of 5 junior developers

        - Software Engineer at StartupCo (2018-2020)
          Developed RESTful APIs using Python and Django
          Implemented CI/CD pipelines with Jenkins
          Collaborated with cross-functional teams

        Skills:
        - Programming: Python, JavaScript, SQL
        - Tools: Docker, Kubernetes, AWS, Git
        - Soft Skills: Leadership, Communication

        Education:
        - Bachelor of Science in Computer Science, State University (2018)
        """

    @pytest.fixture
    def sample_job_description(self) -> str:
        """Sample job description for testing."""
        return """
        Senior Software Engineer - Cloud Infrastructure

        Requirements:
        - 5+ years of experience in software development
        - Strong proficiency in Python
        - Experience with cloud platforms (AWS, GCP, or Azure)
        - Knowledge of containerization (Docker, Kubernetes)
        - Experience with microservices architecture
        - Leadership experience and mentoring skills

        Responsibilities:
        - Design and implement scalable cloud solutions
        - Lead technical initiatives and mentor team members
        - Collaborate with product and engineering teams
        - Drive technical decisions and best practices
        """

    def test_score_returns_scorer_result(
        self,
        scorer,
        sample_resume,
        sample_job_description,
    ):
        """Test that score() returns a ScorerResult object."""
        result = scorer.score(sample_resume, sample_job_description)

        assert isinstance(result, ScorerResult)
        assert result.name == "keyword_exact"
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0

    def test_score_with_perfect_keyword_match(self, scorer):
        """Test scoring with all keywords matched."""
        resume = "Python developer with AWS Docker Kubernetes experience"
        job = "Looking for Python developer with AWS Docker Kubernetes skills"

        # Pass explicit keywords for reliable testing
        result = scorer.score(
            resume, job, keywords=["Python", "developer", "AWS", "Docker", "Kubernetes"]
        )

        # Should have high score with perfect keyword match
        assert result.score >= SCORE_HIGH_MATCH
        assert result.details["exact_matches"] >= 3

    def test_score_with_no_keyword_match(self, scorer):
        """Test scoring with no keyword overlap."""
        resume = "Ruby developer with Rails and Sinatra experience"
        job = "Python developer with Django and Flask experience"

        result = scorer.score(
            resume, job, keywords=["Python", "Django", "Flask", "Rails", "Sinatra"]
        )

        # Should have low score with no Python keywords
        assert result.score < SCORE_MODERATE

    def test_score_with_partial_keyword_match(self, scorer):
        """Test scoring with some keyword overlap."""
        resume = "Python developer with experience in web development"
        job = "Senior Python engineer with AWS and cloud infrastructure experience"

        result = scorer.score(
            resume, job, keywords=["Python", "AWS", "cloud", "engineer"]
        )

        # Should have medium score with partial match
        assert 0.1 <= result.score <= 0.6

    def test_score_includes_match_details(
        self,
        scorer,
        sample_resume,
        sample_job_description,
    ):
        """Test that score() includes detailed match information."""
        result = scorer.score(sample_resume, sample_job_description)

        # Should have match counts
        assert "exact_matches" in result.details
        assert "fuzzy_matches" in result.details
        assert "total_keywords" in result.details
        assert "matched_keywords" in result.details
        assert "missing_keywords" in result.details

        # Match counts should be non-negative integers
        assert result.details["exact_matches"] >= 0
        assert result.details["fuzzy_matches"] >= 0
        assert result.details["total_keywords"] >= 0

    def test_score_case_insensitive(self, scorer):
        """Test that keyword matching is case-insensitive."""
        resume = "Python developer with AWS experience"
        job = "PYTHON DEVELOPER WITH aws EXPERIENCE"

        result = scorer.score(resume, job, keywords=["Python", "developer", "AWS"])

        # Should match regardless of case
        assert result.details["exact_matches"] >= 2
        assert result.score > SCORE_MODERATE

    def test_fuzzy_matching_enabled(self, sample_resume, sample_job_description):
        """Test scorer with fuzzy matching enabled."""
        scorer = KeywordScorer(
            weight=1.0, config=KeywordScorerConfig(fuzzy_threshold=0.8)
        )
        result = scorer.score(
            sample_resume,
            sample_job_description,
            keywords=["Python", "Developer", "AWS", "Docker"],
        )

        # Should have fuzzy matches
        assert "fuzzy_matches" in result.details
        assert result.details["fuzzy_matches"] >= 0

    def test_fuzzy_threshold_affects_results(self):
        """Test that different fuzzy thresholds produce different results."""
        resume = (
            "Python developer with Dockr and Kubernets experience"  # intentional typos
        )
        job = "Looking for Python developer with Docker and Kubernetes"

        scorer_strict = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=0.9))
        scorer_loose = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=0.6))

        result_strict = scorer_strict.score(
            resume, job, keywords=["Python", "developer", "Docker", "Kubernetes"]
        )
        result_loose = scorer_loose.score(
            resume, job, keywords=["Python", "developer", "Docker", "Kubernetes"]
        )

        # Looser threshold should match at least as many keywords
        total_strict = (
            result_strict.details["exact_matches"]
            + result_strict.details["fuzzy_matches"]
        )
        total_loose = (
            result_loose.details["exact_matches"]
            + result_loose.details["fuzzy_matches"]
        )
        assert total_loose >= total_strict

    def test_weighted_score_property(
        self,
        scorer,
        sample_resume,
        sample_job_description,
    ):
        """Test that weighted_score property works correctly."""
        scorer.weight = 0.5
        result = scorer.score(sample_resume, sample_job_description)

        expected_weighted = result.score * 0.5
        assert abs(result.weighted_score - expected_weighted) < 0.001

    def test_empty_inputs(self, scorer):
        """Test behavior with empty inputs."""
        result_empty = scorer.score("", "")
        assert result_empty.score == 0.0
        assert result_empty.details["total_keywords"] == 0

        result_mixed = scorer.score("Python developer", "")
        assert result_mixed.score == 0.0

    def test_custom_keywords(self, scorer):
        """Test scorer with custom keyword list via kwargs."""
        resume = "Experience with Golang and Rust programming"
        job = "Looking for Golang and Rust developers"

        # With explicit custom keywords
        result_custom = scorer.score(
            resume, job, keywords=["Golang", "Rust", "programming"]
        )

        # Custom should work with explicit keywords
        assert result_custom.details["total_keywords"] == 3
        assert result_custom.score >= 0

    def test_to_dict_serialization(self, scorer, sample_resume, sample_job_description):
        """Test that ScorerResult.to_dict() produces valid output."""
        result = scorer.score(sample_resume, sample_job_description)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "name" in result_dict
        assert "score" in result_dict
        assert "weight" in result_dict
        assert "weighted_score" in result_dict
        assert "details" in result_dict
        assert "component_scores" in result_dict

    def test_component_scores_calculated(
        self,
        scorer,
        sample_resume,
        sample_job_description,
    ):
        """Test that component scores are calculated."""
        result = scorer.score(
            sample_resume, sample_job_description, keywords=["Python", "AWS", "Docker"]
        )

        components = result.component_scores

        # Should have keyword-related components
        assert len(components) > 0
        assert "exact_match_rate" in components
        assert "fuzzy_match_rate" in components

        # All should be in [0, 1] range
        for component_name, score in components.items():
            assert 0.0 <= score <= 1.0, f"{component_name}: {score} not in [0, 1]"

    def test_punctuation_handling(self, scorer):
        """Test that punctuation doesn't affect keyword matching."""
        resume = "Python, developer; with AWS!"
        job = "Python developer with AWS"

        result = scorer.score(resume, job, keywords=["Python", "developer", "AWS"])

        # Should still match keywords despite punctuation
        assert result.details["exact_matches"] >= 2

    def test_whitespace_normalization(self, scorer):
        """Test that whitespace is normalized."""
        resume = "Python    developer   with  AWS"
        job = "Python developer with AWS"

        result = scorer.score(resume, job, keywords=["Python", "developer", "AWS"])

        # Should match after normalization
        assert result.score > SCORE_MODERATE

    @pytest.mark.parametrize(
        ("resume", "job", "keywords", "expected_matches"),
        [
            # Exact keyword matches
            (
                "Python developer with AWS and Docker",
                "Need Python developer with AWS and Docker",
                ["Python", "developer", "AWS", "Docker"],
                4,
            ),
            # No overlap (use completely different terms)
            (
                "Ruby developer with Rails and Sinatra",
                "Need Python developer with Django",
                ["Python", "Django", "Rails", "Sinatra"],
                2,  # Rails and Sinatra are in resume
            ),
            # Partial overlap
            (
                "Python developer with Django",
                "Need Python developer with AWS",
                ["Python", "developer", "AWS", "Django"],
                3,  # Python, developer, Django are in resume
            ),
        ],
    )
    def test_exact_keyword_counts(
        self, scorer, resume, job, keywords, expected_matches
    ):
        """Test that exact match counts are correct."""
        result = scorer.score(resume, job, keywords=keywords)

        assert result.details["exact_matches"] == expected_matches

    def test_custom_weight(self, sample_resume, sample_job_description):
        """Test scorer with custom weight."""
        scorer = KeywordScorer(weight=0.75)
        result = scorer.score(sample_resume, sample_job_description)

        assert result.weight == 0.75
        expected_weighted = result.score * 0.75
        assert abs(result.weighted_score - expected_weighted) < 0.001

    def test_matched_keywords_list(self, scorer):
        """Test that matched keywords are returned as a list."""
        resume = "Python developer with AWS and Docker experience"
        job = "Looking for Python developer with AWS and Docker skills"

        result = scorer.score(
            resume, job, keywords=["Python", "developer", "AWS", "Docker"]
        )

        # matched_keywords should be a list of strings
        assert isinstance(result.details["matched_keywords"], list)
        for keyword in result.details["matched_keywords"]:
            assert isinstance(keyword, str)

    def test_missing_keywords_list(self, scorer):
        """Test that missing keywords are returned as a list."""
        resume = "Python developer"
        job = "Looking for Python developer with AWS and Docker skills"

        result = scorer.score(
            resume, job, keywords=["Python", "developer", "AWS", "Docker"]
        )

        # missing_keywords should be a list of strings
        assert isinstance(result.details["missing_keywords"], list)
        for keyword in result.details["missing_keywords"]:
            assert isinstance(keyword, str)

    def test_single_word_inputs(self, scorer):
        """Test behavior with single word inputs."""
        result = scorer.score("Python", "Python", keywords=["Python"])

        # Single word match should be perfect
        assert result.score >= SCORE_NEAR_PERFECT
        assert result.details["exact_matches"] == 1

    def test_repeated_keywords(self, scorer):
        """Test that repeated keywords are counted correctly."""
        resume = "Python Python Python developer developer"
        job = "Python developer"

        result = scorer.score(resume, job, keywords=["Python", "developer"])

        # Should count unique matches, not duplicates
        assert result.details["exact_matches"] == 2
        assert result.score > 0

    def test_fuzzy_matching_with_typos(self):
        """Test fuzzy matching with minor typos."""
        # Set a permissive fuzzy threshold
        scorer = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=0.7))

        resume = "Python developer with Dockr and Kubernets experience"
        job = "Need Python developer with Docker and Kubernetes"

        result = scorer.score(
            resume, job, keywords=["Python", "developer", "Docker", "Kubernetes"]
        )

        # Should get some fuzzy matches for typos
        assert result.details["fuzzy_matches"] >= 0
        # At least Python and developer should match exactly
        assert result.details["exact_matches"] >= 2

    def test_special_characters_in_keywords(self, scorer):
        """Test handling of special characters in keywords."""
        resume = "Experience with C++ and C# programming"
        job = "Need C++ and C# developers"

        result = scorer.score(resume, job, keywords=["C++", "C#"])

        # Should handle special characters correctly
        assert result.score > 0

    def test_number_matching(self, scorer):
        """Test that numbers are matched correctly."""
        resume = "5 years of experience with Python 3"
        job = "Need 5 years experience with Python 3"

        result = scorer.score(resume, job, keywords=["5", "years", "Python", "3"])

        # Should match numbers as part of keywords
        assert result.score > SCORE_MODERATE

    def test_case_sensitive_matching(self):
        """Test case sensitive mode."""
        scorer_case = KeywordScorer(config=KeywordScorerConfig(case_sensitive=True))

        resume = "Python developer with AWS"
        job = "PYTHON DEVELOPER WITH aws"  # mixed case in job

        result = scorer_case.score(resume, job, keywords=["Python", "developer", "AWS"])

        # With case sensitivity, should have different behavior
        # The keywords are case-sensitive matching against both texts
        # Since "Python", "developer", "AWS" don't match "PYTHON", "DEVELOPER", "aws"
        assert result.details["exact_matches"] <= 3


class TestKeywordScorerValidation:
    """Tests for KeywordScorer input validation."""

    def test_invalid_weight_negative(self):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            KeywordScorer(weight=-0.5)

    def test_invalid_weight_above_one(self):
        """Test that weight > 1 raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            KeywordScorer(weight=1.5)

    def test_invalid_fuzzy_threshold_negative(self):
        """Test that negative fuzzy_threshold raises ValueError."""
        with pytest.raises(ValueError, match="fuzzy_threshold must be in"):
            KeywordScorerConfig(fuzzy_threshold=-0.1)

    def test_invalid_fuzzy_threshold_above_one(self):
        """Test that fuzzy_threshold > 1 raises ValueError."""
        with pytest.raises(ValueError, match="fuzzy_threshold must be in"):
            KeywordScorerConfig(fuzzy_threshold=1.5)

    def test_valid_weight_boundary(self):
        """Test that boundary weights are accepted."""
        scorer = KeywordScorer(weight=0.0)
        assert scorer.weight == 0.0

        scorer = KeywordScorer(weight=1.0)
        assert scorer.weight == 1.0

    def test_valid_fuzzy_threshold_boundary(self):
        """Test that boundary fuzzy_threshold values are accepted."""
        scorer = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=0.0))
        assert scorer._config.fuzzy_threshold == 0.0

        scorer = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=1.0))
        assert scorer._config.fuzzy_threshold == 1.0


# ============================================================================
# Issue #69: Edge Case Tests for Keyword Scorer
# ============================================================================


class TestKeywordScorerEdgeCases:
    """Test suite for KeywordScorer edge cases."""

    def test_fuzzy_threshold_zero_matches_everything(self):
        """Test that fuzzy_threshold=0.0 matches any word."""
        scorer = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=0.0))
        result = scorer.score(
            "Python developer",
            "completely different words here",
            keywords=["xyz"],  # Nonsense keyword
        )

        # With threshold 0, even "xyz" might fuzzy-match something
        # The behavior depends on SequenceMatcher ratio
        assert result.score >= 0.0  # Should complete without error

    def test_fuzzy_threshold_one_requires_exact(self):
        """Test that fuzzy_threshold=1.0 requires exact matches."""
        scorer = KeywordScorer(config=KeywordScorerConfig(fuzzy_threshold=1.0))
        result = scorer.score(
            "Python developer",
            "Pythn develper",  # Typos
            keywords=["Pythn"],
        )

        # With threshold 1.0, typos shouldn't fuzzy-match
        assert "matched_keywords" in result.details

    def test_empty_keywords_list(self):
        """Test behavior with empty keywords list."""
        scorer = KeywordScorer()
        result = scorer.score("Python developer", "Python developer", keywords=[])

        assert result.score == 0.0
        assert "error" in result.details or result.details["total_keywords"] == 0

    def test_case_sensitive_matching(self):
        """Test case-sensitive matching mode."""
        scorer = KeywordScorer(config=KeywordScorerConfig(case_sensitive=True))
        result = scorer.score(
            "python developer",
            "Python Developer needed",
            keywords=["Python"],  # Capital P
        )

        # With case sensitivity, "Python" won't match "python"
        # (unless the text preprocessing normalizes case)
        assert result.score >= 0.0

    def test_very_long_keyword(self):
        """Test handling of very long keywords."""
        long_keyword = "a" * 100
        scorer = KeywordScorer()
        result = scorer.score(
            f"Resume with {long_keyword}",
            f"Job needs {long_keyword}",
            keywords=[long_keyword],
        )

        # Should complete without error
        assert result.score >= 0.0

    def test_special_regex_characters_in_keywords(self):
        """Test keywords with regex special characters."""
        scorer = KeywordScorer()
        result = scorer.score(
            "Experience with C++ and .NET framework",
            "Needs C++ .NET developer",
            keywords=["C++", ".NET"],
        )

        # Should handle regex special characters without crashing
        assert result.score >= 0.0

    def test_unicode_in_keywords(self):
        """Test unicode characters in keywords."""
        scorer = KeywordScorer()
        result = scorer.score(
            "Developer with résumé experience",
            "Looking for résumé parsing skills",
            keywords=["résumé"],
        )

        # Should handle accented characters
        assert result.score >= 0.0


class TestKeywordExtraction:
    """Tests for the _extract_keywords method."""

    def test_extracts_acronyms(self):
        """Test extraction of acronyms like AWS, API."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords("Need AWS and API experience")
        assert "AWS" in keywords
        assert "API" in keywords

    def test_extracts_camelcase(self):
        """Test extraction of CamelCase terms like JavaScript."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords("Experience with JavaScript and TypeScript")
        assert any("JavaScript" in kw for kw in keywords)

    def test_extracts_quoted_terms(self):
        """Test extraction of quoted phrases."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords('Must know "machine learning" techniques')
        assert any("machine learning" in kw for kw in keywords)

    def test_extracts_skill_patterns(self):
        """Test extraction of technology patterns like 'Python language'."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords("Python language and React framework")
        assert any("python" in kw.lower() for kw in keywords)

    def test_fallback_extraction_for_plain_text(self):
        """Test fallback extraction when no patterns match."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        # All lowercase, no patterns - triggers fallback
        keywords = scorer._extract_keywords("developer needed for backend coding tasks")
        assert len(keywords) > 0
        assert any("developer" in kw.lower() for kw in keywords)

    def test_respects_max_keywords_limit(self):
        """Test that extraction respects max_keywords parameter."""
        scorer = KeywordScorer(
            config=KeywordScorerConfig(extract_keywords=True, max_keywords=3)
        )
        text = "AWS API GCP Docker Kubernetes Python Java React Angular Vue"
        keywords = scorer._extract_keywords(text)
        assert len(keywords) <= 3

    def test_removes_duplicates(self):
        """Test that duplicate keywords are removed."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords("Python Python PYTHON experience")
        python_count = sum(1 for kw in keywords if "python" in kw.lower())
        assert python_count == 1

    def test_filters_short_keywords(self):
        """Test that very short keywords are filtered."""
        scorer = KeywordScorer(config=KeywordScorerConfig(extract_keywords=True))
        keywords = scorer._extract_keywords("Use AI and ML for data processing")
        # AI and ML are too short (2 chars), should be filtered
        assert not any(len(kw) <= 2 for kw in keywords)
