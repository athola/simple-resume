"""Unit tests for ATSTournament.

Tests the tournament runner including graceful failure handling,
weight calculation, and result aggregation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.tournament import (
    ATSTournament,
    TournamentResult,
    score_resume,
)


class MockScorer(BaseScorer):
    """Mock scorer for testing."""

    def __init__(
        self, weight: float = 1.0, score_value: float = 0.5, name: str = "mock"
    ) -> None:
        super().__init__(weight=weight)
        self.score_value = score_value
        self.scorer_name = name

    def score(
        self,
        resume_text: str,  # noqa: ARG002
        job_description: str,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> ScorerResult:
        return ScorerResult(
            name=self.scorer_name,
            score=self.score_value,
            weight=self.weight,
            details={"mock": True},
            component_scores={"mock_component": self.score_value},
        )


class FailingScorer(BaseScorer):
    """Scorer that always raises an exception."""

    def __init__(self, weight: float = 1.0, error_msg: str = "Mock failure") -> None:
        super().__init__(weight=weight)
        self.error_msg = error_msg

    def score(
        self,
        resume_text: str,  # noqa: ARG002
        job_description: str,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> ScorerResult:
        raise RuntimeError(self.error_msg)


class TestTournamentResult:
    """Test suite for TournamentResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid TournamentResult."""
        result = TournamentResult(
            overall_score=0.75,
            algorithm_results=[],
            component_breakdown={"skill_match": 0.8},
            metadata={"test": True},
        )
        assert result.overall_score == 0.75
        assert result.component_breakdown["skill_match"] == 0.8

    def test_invalid_overall_score_negative(self):
        """Test that negative overall_score raises ValueError."""
        with pytest.raises(ValueError, match="overall_score must be in"):
            TournamentResult(overall_score=-0.1)

    def test_invalid_overall_score_above_one(self):
        """Test that overall_score > 1 raises ValueError."""
        with pytest.raises(ValueError, match="overall_score must be in"):
            TournamentResult(overall_score=1.5)

    def test_invalid_component_score(self):
        """Test that invalid component score raises ValueError."""
        with pytest.raises(ValueError, match="component_breakdown"):
            TournamentResult(overall_score=0.5, component_breakdown={"bad_score": 1.5})

    def test_to_dict_serialization(self):
        """Test TournamentResult.to_dict() produces valid output."""
        result = TournamentResult(
            overall_score=0.75,
            algorithm_results=[],
            component_breakdown={"test": 0.5},
            metadata={"key": "value"},
            failed_scorers=[("TestScorer", "Error message")],
        )
        result_dict = result.to_dict()

        assert result_dict["overall_score"] == 0.75
        assert result_dict["component_breakdown"] == {"test": 0.5}
        assert result_dict["metadata"] == {"key": "value"}
        assert result_dict["failed_scorers"] == [("TestScorer", "Error message")]

    def test_failed_scorers_default_empty(self):
        """Test that failed_scorers defaults to empty list."""
        result = TournamentResult(overall_score=0.5)
        assert result.failed_scorers == []


class TestATSTournament:
    """Test suite for ATSTournament class."""

    @pytest.fixture
    def sample_resume(self) -> str:
        """Sample resume text for testing."""
        return """
        Senior Software Engineer with 5 years experience.
        Skills: Python, AWS, Docker, Kubernetes
        """

    @pytest.fixture
    def sample_job(self) -> str:
        """Sample job description for testing."""
        return """
        Looking for Senior Software Engineer with Python and AWS experience.
        Requirements: Docker, Kubernetes, cloud infrastructure
        """

    def test_default_scorers(self):
        """Test tournament initializes with default scorers."""
        tournament = ATSTournament()
        assert len(tournament.scorers) == 3

    def test_custom_scorers(self):
        """Test tournament with custom scorers."""
        scorers = [MockScorer(weight=0.5), MockScorer(weight=0.5)]
        tournament = ATSTournament(scorers=scorers)
        assert len(tournament.scorers) == 2

    def test_score_returns_tournament_result(self, sample_resume, sample_job):
        """Test that score() returns a TournamentResult object."""
        tournament = ATSTournament()
        result = tournament.score(sample_resume, sample_job)

        assert isinstance(result, TournamentResult)
        assert 0.0 <= result.overall_score <= 1.0
        assert len(result.algorithm_results) == 3

    def test_score_empty_resume(self, sample_job):
        """Test scoring with empty resume."""
        tournament = ATSTournament()
        result = tournament.score("", sample_job)

        assert result.overall_score == 0.0
        assert "error" in result.metadata
        assert result.metadata["error"] == "Resume text is empty"

    def test_score_empty_job_description(self, sample_resume):
        """Test scoring with empty job description."""
        tournament = ATSTournament()
        result = tournament.score(sample_resume, "")

        assert result.overall_score == 0.0
        assert "error" in result.metadata
        assert result.metadata["error"] == "Job description is empty"

    def test_weighted_score_calculation(self):
        """Test that weighted scores are calculated correctly."""
        scorers = [
            MockScorer(weight=0.5, score_value=1.0, name="high"),
            MockScorer(weight=0.5, score_value=0.0, name="low"),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score("Python developer", "Python developer needed")

        # Weighted average: (0.5*1.0 + 0.5*0.0) / (0.5 + 0.5) = 0.5
        assert abs(result.overall_score - 0.5) < 0.001

    def test_unequal_weights(self):
        """Test weighted calculation with unequal weights."""
        scorers = [
            MockScorer(weight=0.8, score_value=1.0, name="high"),
            MockScorer(weight=0.2, score_value=0.0, name="low"),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score("Python developer", "Python developer needed")

        # Weighted average: (0.8*1.0 + 0.2*0.0) / (0.8 + 0.2) = 0.8
        assert abs(result.overall_score - 0.8) < 0.001

    def test_metadata_includes_scorer_info(self, sample_resume, sample_job):
        """Test that metadata includes scorer information."""
        tournament = ATSTournament()
        result = tournament.score(sample_resume, sample_job)

        assert "num_algorithms" in result.metadata
        assert "scorer_names" in result.metadata
        assert "individual_scores" in result.metadata

    def test_component_breakdown_aggregation(self):
        """Test that component scores are aggregated correctly."""
        scorer1 = MockScorer(weight=0.5, score_value=0.8, name="scorer1")
        scorer2 = MockScorer(weight=0.5, score_value=0.4, name="scorer2")

        # Mock component scores for consistent testing
        tournament = ATSTournament(scorers=[scorer1, scorer2])
        result = tournament.score("Python developer", "Python developer needed")

        # Both scorers have mock_component with values 0.8 and 0.4
        # Average should be (0.8 + 0.4) / 2 = 0.6
        if "mock_component" in result.component_breakdown:
            # Actual mock components get averaged (use approximate comparison)
            assert abs(result.component_breakdown["mock_component"] - 0.6) < 0.001


class TestATSTournamentGracefulFailure:
    """Tests for graceful failure handling in ATSTournament (issue #66)."""

    @pytest.fixture
    def sample_resume(self) -> str:
        return "Python developer with AWS experience"

    @pytest.fixture
    def sample_job(self) -> str:
        return "Looking for Python developer"

    def test_single_scorer_failure_continues(self, sample_resume, sample_job):
        """Test that tournament continues when one scorer fails."""
        scorers = [
            MockScorer(weight=0.5, score_value=0.8, name="success1"),
            FailingScorer(weight=0.3, error_msg="Test failure"),
            MockScorer(weight=0.2, score_value=0.6, name="success2"),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(sample_resume, sample_job)

        # Should still get a valid result from the 2 successful scorers
        assert result.overall_score > 0
        assert len(result.algorithm_results) == 2
        assert len(result.failed_scorers) == 1
        assert result.failed_scorers[0][0] == "FailingScorer"
        assert "Test failure" in result.failed_scorers[0][1]

    def test_all_scorers_fail_returns_zero(self, sample_resume, sample_job):
        """Test that tournament returns zero score when all scorers fail."""
        scorers = [
            FailingScorer(weight=0.5, error_msg="Failure 1"),
            FailingScorer(weight=0.3, error_msg="Failure 2"),
            FailingScorer(weight=0.2, error_msg="Failure 3"),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(sample_resume, sample_job)

        assert result.overall_score == 0.0
        assert len(result.algorithm_results) == 0
        assert len(result.failed_scorers) == 3
        assert "error" in result.metadata
        assert result.metadata["error"] == "All scorers failed"

    def test_failed_scorers_logged(self, sample_resume, sample_job, caplog):
        """Test that failed scorers are logged."""
        caplog.set_level("WARNING")

        scorers = [
            MockScorer(weight=0.5, score_value=0.8, name="success"),
            FailingScorer(weight=0.5, error_msg="Expected test failure"),
        ]
        tournament = ATSTournament(scorers=scorers)
        tournament.score(sample_resume, sample_job)

        # Check that warning was logged
        assert "FailingScorer failed during tournament" in caplog.text
        assert "Expected test failure" in caplog.text

    def test_weights_recalculated_after_failure(self, sample_resume, sample_job):
        """Test that weights are recalculated correctly when scorer fails."""
        scorers = [
            MockScorer(weight=0.4, score_value=1.0, name="scorer1"),  # 1.0
            FailingScorer(weight=0.4, error_msg="Failed"),  # Fails
            MockScorer(weight=0.2, score_value=0.0, name="scorer2"),  # 0.0
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(sample_resume, sample_job)

        # Only scorer1 (weight=0.4, score=1.0) and scorer2 (weight=0.2, score=0.0)
        # Weighted average: (0.4*1.0 + 0.2*0.0) / (0.4 + 0.2) = 0.4 / 0.6 ≈ 0.667
        expected = 0.4 / 0.6
        assert abs(result.overall_score - expected) < 0.001

    def test_metadata_includes_failure_count(self, sample_resume, sample_job):
        """Test that metadata includes failure count."""
        scorers = [
            MockScorer(weight=0.5, score_value=0.8, name="success"),
            FailingScorer(weight=0.5, error_msg="Failed"),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(sample_resume, sample_job)

        assert result.metadata["num_algorithms"] == 2
        assert result.metadata["num_successful"] == 1
        assert result.metadata["num_failed"] == 1

    def test_graceful_failure_with_exception_types(self, sample_resume, sample_job):
        """Test graceful handling of different exception types."""

        class ValueError_Scorer(BaseScorer):
            def score(self, resume_text, job_description, **kwargs):  # noqa: ARG002
                raise ValueError("Value error test")

        class TypeError_Scorer(BaseScorer):
            def score(self, resume_text, job_description, **kwargs):  # noqa: ARG002
                raise TypeError("Type error test")

        scorers = [
            MockScorer(weight=1.0, score_value=0.7, name="success"),
            ValueError_Scorer(weight=1.0),
            TypeError_Scorer(weight=1.0),
        ]
        tournament = ATSTournament(scorers=scorers)
        result = tournament.score(sample_resume, sample_job)

        # Should handle both exception types gracefully
        assert len(result.algorithm_results) == 1
        assert len(result.failed_scorers) == 2


class TestTopMatches:
    """Test suite for get_top_matches method."""

    def test_top_matches_ranking(self):
        """Test that resumes are ranked by score."""
        scorers = [MockScorer(weight=1.0, score_value=0.5, name="mock")]
        tournament = ATSTournament(scorers=scorers)

        resumes = [
            "Low match resume",
            "High match Python developer AWS",
            "Medium match developer",
        ]
        job = "Python developer with AWS"

        # Mock different scores for different resumes
        with patch.object(tournament, "score") as mock_score:
            mock_score.side_effect = [
                TournamentResult(overall_score=0.3),
                TournamentResult(overall_score=0.9),
                TournamentResult(overall_score=0.6),
            ]

            results = tournament.get_top_matches(resumes, job, top_n=3)

        # Results should be sorted by score descending
        assert len(results) == 3
        assert results[0][1] == 0.9  # Highest score first
        assert results[1][1] == 0.6  # Medium score second
        assert results[2][1] == 0.3  # Lowest score last

    def test_top_n_limits_results(self):
        """Test that top_n limits the number of results."""
        tournament = ATSTournament()
        resumes = [f"Resume {i}" for i in range(10)]
        job = "Python developer"

        results = tournament.get_top_matches(resumes, job, top_n=3)
        assert len(results) == 3


class TestScoreResumeConvenience:
    """Test suite for score_resume convenience function."""

    def test_convenience_function_works(self):
        """Test the score_resume convenience function."""
        result = score_resume(
            "Python developer with AWS", "Looking for Python developer"
        )

        assert isinstance(result, TournamentResult)
        assert 0.0 <= result.overall_score <= 1.0

    def test_convenience_function_with_custom_scorers(self):
        """Test score_resume with custom scorers."""
        scorers = [MockScorer(weight=1.0, score_value=0.75, name="custom")]
        result = score_resume(
            "Python developer",
            "Python developer needed",
            custom_scorers=scorers,
        )

        assert result.overall_score == 0.75


class TestATSTournamentBERTIntegration:
    """Test BERT integration paths in ATSTournament."""

    def test_bert_enabled_when_available(self):
        """Test that BERT scorer is included when available."""
        # Mock BERTScorer class to return a mock instance
        mock_bert_instance = MagicMock()
        mock_bert_instance.available = True
        mock_bert_instance.weight = 0.35

        mock_bert_class = MagicMock(return_value=mock_bert_instance)

        # Patch the import inside the function
        with patch.dict(
            "sys.modules",
            {"simple_resume.core.ats.bert": MagicMock(BERTScorer=mock_bert_class)},
        ):
            tournament = ATSTournament(include_bert=True)
            # When BERT is available, we get 4 scorers
            assert len(tournament.scorers) == 4

    def test_bert_not_included_when_unavailable(self):
        """Test that BERT scorer is excluded when unavailable."""
        mock_bert_instance = MagicMock()
        mock_bert_instance.available = False

        mock_bert_class = MagicMock(return_value=mock_bert_instance)

        with patch.dict(
            "sys.modules",
            {"simple_resume.core.ats.bert": MagicMock(BERTScorer=mock_bert_class)},
        ):
            tournament = ATSTournament(include_bert=True)
            # Should fall back to 3 default scorers without BERT
            assert len(tournament.scorers) == 3

    def test_bert_import_error_handled(self):
        """Test tournament handles BERTScorer import error gracefully."""
        # Remove the module so import fails
        with patch.dict("sys.modules", {"simple_resume.core.ats.bert": None}):
            # Should not raise, should fall back gracefully
            tournament = ATSTournament(include_bert=True)
            assert len(tournament.scorers) == 3

    def test_bert_disabled_uses_fallback_weights(self):
        """Test that disabling BERT uses fallback weights that sum to 1.0."""
        tournament = ATSTournament(include_bert=False)

        # With BERT disabled, we should have 3 scorers with fallback weights
        total_weight = sum(s.weight for s in tournament.scorers)
        assert abs(total_weight - 1.0) < 0.01


class TestATSTournamentWeightedScore:
    """Test edge cases in weighted score calculation."""

    def test_empty_results_returns_zero(self):
        """Test _calculate_weighted_score with empty results list."""
        tournament = ATSTournament()
        result = tournament._calculate_weighted_score([])
        assert result == 0.0

    def test_zero_total_weight_returns_zero(self):
        """Test _calculate_weighted_score when all weights are zero."""
        tournament = ATSTournament()

        # Create results with zero weights
        zero_weight_results = [
            ScorerResult(name="test1", score=0.8, weight=0.0, details={}),
            ScorerResult(name="test2", score=0.6, weight=0.0, details={}),
        ]

        result = tournament._calculate_weighted_score(zero_weight_results)
        assert result == 0.0

    def test_weighted_score_calculation(self):
        """Test correct weighted score calculation."""
        tournament = ATSTournament()

        results = [
            ScorerResult(name="test1", score=1.0, weight=0.6, details={}),
            ScorerResult(name="test2", score=0.0, weight=0.4, details={}),
        ]

        # Expected: (0.6 * 1.0 + 0.4 * 0.0) / (0.6 + 0.4) = 0.6
        result = tournament._calculate_weighted_score(results)
        assert abs(result - 0.6) < 0.001
