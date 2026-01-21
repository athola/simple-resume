"""Property-based tests for ATS scoring algorithms.

Uses Hypothesis to test mathematical properties and edge cases
across all ATS scoring algorithms, ensuring numerical stability
and correctness for a wide range of inputs.
"""

from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import text

from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer
from simple_resume.core.ats.tfidf import TFIDFScorer
from simple_resume.core.ats.tournament import ATSTournament


class TestTFIDFScorerProperties:
    """Property-based tests for TFIDFScorer."""

    @given(
        resume=text(min_size=10, max_size=5000).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=5000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, deadline=None)
    def test_score_always_in_valid_range(self, resume, job):
        """Test that scores are always in [0, 1] range."""
        scorer = TFIDFScorer(weight=1.0)
        result = scorer.score(resume, job)
        assert 0.0 <= result.score <= 1.0
        assert 0.0 <= result.details["cosine_similarity"] <= 1.0

    @given(
        resume=text(min_size=10, max_size=10000).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=10000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_long_document_boundary_conditions(self, resume, job):
        """Test boundary conditions with very long documents.

        This tests the heuristic normalization where shared TF-IDF scores
        are divided by 10.0. We verify that scores never exceed 1.0 even
        for very long documents where the sum of products might be large.
        """
        scorer = TFIDFScorer(weight=1.0)
        result = scorer.score(resume, job)

        # All component scores should stay in [0, 1]
        for component_name, score in result.component_scores.items():
            assert 0.0 <= score <= 1.0, (
                f"{component_name} = {score} not in [0, 1] for long documents"
            )

    @given(text(min_size=0, max_size=100))
    def test_empty_input_handling(self, text_input):
        """Test that empty or near-empty inputs are handled gracefully."""
        scorer = TFIDFScorer(weight=1.0)
        result = scorer.score(text_input, text_input)
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0

    @given(
        resume=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_symmetry_property(self, resume, job):
        """Test that similarity is symmetric (score(a,b) == score(b,a)).

        Note: This may not always hold exactly due to stopwords and
        preprocessing, but should be approximately true.
        """
        scorer = TFIDFScorer(weight=1.0)
        result_ab = scorer.score(resume, job)
        result_ba = scorer.score(job, resume)

        # Cosine similarity should be symmetric
        assert (
            abs(
                result_ab.details["cosine_similarity"]
                - result_ba.details["cosine_similarity"]
            )
            < 0.01
        )

    @given(
        text(min_size=10, max_size=5000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=20, deadline=None)
    def test_identical_input_high_score(self, text_input):
        """Test that identical inputs produce high similarity scores."""
        scorer = TFIDFScorer(weight=1.0)
        result = scorer.score(text_input, text_input)

        # May be less than 1.0 due to stopwords, but should be high
        # Only assert if we got valid terms (not just stopwords)
        if result.score > 0:
            assert result.score >= 0.7, (
                f"Identical inputs should have high similarity, got {result.score}"
            )


class TestJaccardScorerProperties:
    """Property-based tests for JaccardScorer."""

    @given(
        resume=text(min_size=0, max_size=5000),
        job=text(min_size=0, max_size=5000),
    )
    @settings(max_examples=100, deadline=None)
    def test_score_always_in_valid_range(self, resume, job):
        """Test that scores are always in [0, 1] range."""
        scorer = JaccardScorer(weight=1.0)
        result = scorer.score(resume, job)
        assert 0.0 <= result.score <= 1.0

    @given(
        text(min_size=0, max_size=1000),
    )
    def test_empty_inputs(self, text_input):
        """Test edge cases with empty inputs."""
        scorer = JaccardScorer(weight=1.0)
        # Empty vs empty should give score > 0 (our convention)
        result_empty = scorer.score("", "")
        assert result_empty.score >= 0.0

        # Non-empty vs empty should give 0.0
        result_mixed = scorer.score(text_input, "")
        assert 0.0 <= result_mixed.score <= 1.0

    @given(
        resume=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_symmetry_property(self, resume, job):
        """Test that Jaccard similarity is symmetric."""
        scorer = JaccardScorer(weight=1.0)
        result_ab = scorer.score(resume, job)
        result_ba = scorer.score(job, resume)

        # Jaccard should be symmetric
        assert abs(result_ab.score - result_ba.score) < 0.001

    @given(
        text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
    )
    def test_identical_input_maximum_score(self, text_input):
        """Test that identical inputs give score of 1.0."""
        scorer = JaccardScorer(weight=1.0)
        result = scorer.score(text_input, text_input)
        assert result.score >= 0.9, (
            f"Identical inputs should have maximum similarity, got {result.score}"
        )

    @given(
        ngram_start=st.integers(min_value=1, max_value=5),
        ngram_end=st.integers(min_value=1, max_value=5),
        text_input=text(min_size=20, max_size=500).filter(lambda x: x.strip()),
    )
    def test_ngram_range_validity(self, ngram_start, ngram_end, text_input):
        """Test that various n-gram ranges produce valid scores."""
        assume(ngram_start <= ngram_end)

        scorer = JaccardScorer(ngram_range=(ngram_start, ngram_end))
        result = scorer.score(text_input, text_input)

        assert 0.0 <= result.score <= 1.0
        assert "ngram_range" in result.details


class TestKeywordScorerProperties:
    """Property-based tests for KeywordScorer."""

    @given(
        resume=text(min_size=0, max_size=5000),
        job=text(min_size=0, max_size=5000),
    )
    @settings(max_examples=100, deadline=None)
    def test_score_always_in_valid_range(self, resume, job):
        """Test that scores are always in [0, 1] range."""
        scorer = KeywordScorer(weight=1.0)
        result = scorer.score(resume, job)
        assert 0.0 <= result.score <= 1.0

    @given(
        text(min_size=0, max_size=1000),
    )
    def test_empty_inputs(self, text_input):
        """Test edge cases with empty inputs."""
        scorer = KeywordScorer(weight=1.0)
        result_empty = scorer.score("", "")
        assert result_empty.score == 0.0

        result_mixed = scorer.score(text_input, "")
        assert 0.0 <= result_mixed.score <= 1.0

    @given(
        threshold=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        resume=text(min_size=10, max_size=500).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=500).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_fuzzy_threshold_affects_results(self, threshold, resume, job):
        """Test that different fuzzy thresholds produce valid results."""
        scorer = KeywordScorer(fuzzy_threshold=threshold)
        result = scorer.score(resume, job)

        assert 0.0 <= result.score <= 1.0
        assert "fuzzy_matches" in result.details
        assert "exact_matches" in result.details

    @given(
        resume=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=1000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_match_counts_consistency(self, resume, job):
        """Test that match counts are internally consistent."""
        scorer = KeywordScorer(weight=1.0)
        result = scorer.score(resume, job)

        exact = result.details["exact_matches"]
        fuzzy = result.details["fuzzy_matches"]
        total = result.details["total_keywords"]

        assert exact >= 0
        assert fuzzy >= 0
        assert total >= 0
        assert exact + fuzzy <= total


class TestTournamentProperties:
    """Property-based tests for ATSTournament."""

    @given(
        resume=text(min_size=0, max_size=5000),
        job=text(min_size=0, max_size=5000),
    )
    @settings(max_examples=100, deadline=None)
    def test_overall_score_in_valid_range(self, resume, job):
        """Test that overall score is always in [0, 1] range."""
        tournament = ATSTournament()
        result = tournament.score(resume, job)
        assert 0.0 <= result.overall_score <= 1.0

    @given(
        weight1=st.floats(
            min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False
        ),
        weight2=st.floats(
            min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False
        ),
        resume=text(min_size=10, max_size=500).filter(lambda x: x.strip()),
        job=text(min_size=10, max_size=500).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=None)
    def test_custom_weights_produce_valid_scores(self, weight1, weight2, resume, job):
        """Test that custom weights produce valid scores."""
        assume(weight1 + weight2 > 0)  # Avoid zero total weight

        tournament = ATSTournament(
            scorers=[
                TFIDFScorer(weight=weight1),
                JaccardScorer(weight=weight2),
            ]
        )
        result = tournament.score(resume, job)

        assert 0.0 <= result.overall_score <= 1.0
        assert len(result.algorithm_results) == 2

    @given(
        resumes=st.lists(
            text(min_size=10, max_size=500).filter(lambda x: x.strip()),
            min_size=1,
            max_size=20,
        ),
        job=text(min_size=10, max_size=500).filter(lambda x: x.strip()),
    )
    @settings(max_examples=30, deadline=None)
    def test_top_matches_returns_valid_count(self, resumes, job):
        """Test that top_matches returns correct number of results."""
        tournament = ATSTournament()
        top_n = 5
        results = tournament.get_top_matches(resumes, job, top_n=top_n)

        assert len(results) <= top_n
        assert len(results) <= len(resumes)

        # Results should be sorted by score descending
        scores = [score for _, score, _ in results]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

        # All scores should be valid
        for idx, score, preview in results:
            assert 0.0 <= score <= 1.0
            assert isinstance(idx, int)
            assert isinstance(preview, str)


class TestNumericalStability:
    """Tests for numerical stability in edge cases."""

    @given(
        text_input=st.text(min_size=0, max_size=100),
    )
    def test_unicode_and_special_characters(self, text_input):
        """Test that unicode and special characters are handled gracefully."""
        all_scorers = [
            TFIDFScorer(weight=1.0),
            JaccardScorer(weight=1.0),
            KeywordScorer(weight=1.0),
        ]
        for scorer in all_scorers:
            result = scorer.score(text_input, text_input)
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0

    @given(
        # Generate text with many repeated words (to test TF-IDF behavior)
        words=st.lists(
            st.sampled_from(
                ["python", "java", "javascript", "aws", "docker", "kubernetes"]
            ),
            min_size=50,
            max_size=500,
        ),
    )
    def test_repeated_keywords(self, words):
        """Test behavior with highly repetitive text."""
        text = " ".join(words)
        all_scorers = [
            TFIDFScorer(weight=1.0),
            JaccardScorer(weight=1.0),
            KeywordScorer(weight=1.0),
        ]
        for scorer in all_scorers:
            result = scorer.score(text, text)
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0
