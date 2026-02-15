"""Integration tests for the ATS scoring pipeline.

Tests the full scoring pipeline from raw text through tournament
scoring, validating that all components work together correctly.
"""

from __future__ import annotations

from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer, KeywordScorerConfig
from simple_resume.core.ats.tfidf import TFIDFScorer
from simple_resume.core.ats.tournament import (
    ATSTournament,
    TournamentResult,
    score_resume,
)

SAMPLE_RESUME = """
John Smith
Senior Software Engineer

Skills: Python, JavaScript, React, Docker, Kubernetes, AWS, PostgreSQL, Redis

Experience:
- Led team of 5 engineers building microservices architecture
- Implemented CI/CD pipelines using GitHub Actions and Docker
- Designed RESTful APIs serving 10M+ requests/day
- Managed PostgreSQL databases with complex query optimization

Education:
BS Computer Science, MIT
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Software Engineer - Backend

Requirements:
- 5+ years experience with Python
- Experience with Docker and Kubernetes
- Strong understanding of RESTful API design
- Database experience (PostgreSQL preferred)
- CI/CD pipeline experience
- Experience leading engineering teams

Nice to have:
- AWS experience
- Microservices architecture
- Redis or similar caching solutions
"""


class TestATSScoringPipeline:
    """Integration tests for ATS scoring end-to-end."""

    def test_tournament_produces_valid_result(self) -> None:
        """Full tournament run with all default scorers produces a valid result."""
        tournament = ATSTournament(include_bert=False)
        result = tournament.score(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION)

        assert isinstance(result, TournamentResult)
        assert 0.0 <= result.overall_score <= 1.0
        assert len(result.algorithm_results) > 0
        assert result.metadata["num_successful"] > 0
        assert result.metadata["num_failed"] == 0

    def test_score_resume_convenience_function(self) -> None:
        """score_resume convenience function works end-to-end."""
        result = score_resume(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION, percentage=True)

        assert isinstance(result, TournamentResult)
        assert 0.0 <= result.overall_score <= 1.0
        assert "percentage_score" in result.metadata
        assert 0.0 <= result.metadata["percentage_score"] <= 100.0

    def test_keyword_scorer_finds_matching_keywords(self) -> None:
        """KeywordScorer extracts and matches keywords across documents."""
        scorer = KeywordScorer(weight=1.0)
        result = scorer.score(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION)

        assert result.score > 0.0
        details = result.details
        assert details["exact_matches"] > 0
        assert details["total_keywords"] > 0
        assert len(details["matched_keywords"]) > 0

    def test_tfidf_scorer_produces_result(self) -> None:
        """TFIDFScorer produces a valid result with expected details."""
        scorer = TFIDFScorer(weight=1.0)
        result = scorer.score(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION)

        assert 0.0 <= result.score <= 1.0
        assert "cosine_similarity" in result.details
        assert "top_job_keywords" in result.details

    def test_jaccard_scorer_produces_overlap(self) -> None:
        """JaccardScorer produces non-zero overlap for related documents."""
        scorer = JaccardScorer(weight=1.0)
        result = scorer.score(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION)

        assert result.score > 0.0

    def test_tournament_with_custom_scorers(self) -> None:
        """Tournament works with custom scorer list."""
        scorers = [
            KeywordScorer(weight=0.5),
            TFIDFScorer(weight=0.5),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(SAMPLE_RESUME, SAMPLE_JOB_DESCRIPTION)

        assert len(result.algorithm_results) == 2
        assert result.metadata["num_algorithms"] == 2

    def test_empty_inputs_return_zero_score(self) -> None:
        """Empty inputs produce zero score without errors."""
        result = score_resume("", SAMPLE_JOB_DESCRIPTION)
        assert result.overall_score == 0.0
        assert "error" in result.metadata

        result = score_resume(SAMPLE_RESUME, "")
        assert result.overall_score == 0.0
        assert "error" in result.metadata

    def test_keyword_fuzzy_matching_catches_typos(self) -> None:
        """Fuzzy matching finds near-matches (e.g., spelling variations)."""
        config = KeywordScorerConfig(fuzzy_threshold=0.8)
        scorer = KeywordScorer(weight=1.0, config=config)

        resume = "Experience with Kuberntes and Dokcer containers"
        job = "Must know Kubernetes and Docker"

        result = scorer.score(resume, job)
        # Fuzzy matching should catch "Kuberntes" ≈ "Kubernetes"
        assert (
            result.details["fuzzy_matches"] > 0 or result.details["exact_matches"] > 0
        )

    def test_top_matches_ranks_resumes_correctly(self) -> None:
        """get_top_matches ranks relevant resumes higher than irrelevant ones."""
        tournament = ATSTournament(include_bert=False)
        resumes = [
            "I am a chef with 10 years of culinary experience.",
            SAMPLE_RESUME,
            "Marketing specialist with social media expertise.",
        ]
        results = tournament.get_top_matches(resumes, SAMPLE_JOB_DESCRIPTION, top_n=3)

        assert len(results) == 3
        # The relevant resume (index 1) should rank highest
        assert results[0][0] == 1, (
            f"Expected relevant resume (idx=1) to rank first, got idx={results[0][0]}"
        )
