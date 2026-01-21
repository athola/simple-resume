"""Tournament runner for multi-algorithm ATS scoring.

Runs multiple scoring algorithms in parallel and aggregates results
using weighted averages to produce a comprehensive resume-job match score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer
from simple_resume.core.ats.tfidf import TFIDFScorer


@dataclass
class TournamentResult:
    """Result from running multiple scoring algorithms.

    Attributes:
        overall_score: Final weighted average score (0-1)
        algorithm_results: Results from each individual algorithm
        component_breakdown: Scores by rubric component
        metadata: Additional tournament metadata

    """

    overall_score: float
    algorithm_results: list[ScorerResult] = field(default_factory=list)
    component_breakdown: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "algorithm_results": [r.to_dict() for r in self.algorithm_results],
            "component_breakdown": self.component_breakdown,
            "metadata": self.metadata,
        }


class ATSTournament:
    """Runs multiple ATS scoring algorithms in tournament style.

    Each algorithm provides an independent assessment of resume-job
    compatibility. Results are combined using weighted averages to
    produce a robust, comprehensive score.
    """

    def __init__(
        self,
        scorers: list[BaseScorer] | None = None,
    ) -> None:
        """Initialize the tournament with a list of scorers.

        Args:
            scorers: List of scoring algorithms to use. If None, uses default set.

        """
        if scorers is None:
            # Default scorers with weights from refined rubric
            self.scorers = [
                TFIDFScorer(weight=0.40),  # Primary scorer
                JaccardScorer(weight=0.30),  # Phrase matching
                KeywordScorer(weight=0.30),  # Exact keywords
            ]
        else:
            self.scorers = scorers

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> TournamentResult:
        """Score resume against job description using all tournament algorithms.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters passed to all scorers

        Returns:
            TournamentResult with aggregated score and breakdown

        """
        # Validate inputs
        if not resume_text or not resume_text.strip():
            return TournamentResult(
                overall_score=0.0,
                algorithm_results=[],
                component_breakdown={},
                metadata={"error": "Resume text is empty"},
            )

        if not job_description or not job_description.strip():
            return TournamentResult(
                overall_score=0.0,
                algorithm_results=[],
                component_breakdown={},
                metadata={"error": "Job description is empty"},
            )

        algorithm_results = []

        # Run each scorer
        for scorer in self.scorers:
            result = scorer.score(resume_text, job_description, **kwargs)
            algorithm_results.append(result)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(algorithm_results)

        # Aggregate component scores across algorithms
        component_breakdown = self._aggregate_component_scores(algorithm_results)

        # Extract metadata
        metadata = {
            "num_algorithms": len(self.scorers),
            "scorer_names": [r.name for r in algorithm_results],
            "individual_scores": [r.score for r in algorithm_results],
        }

        return TournamentResult(
            overall_score=overall_score,
            algorithm_results=algorithm_results,
            component_breakdown=component_breakdown,
            metadata=metadata,
        )

    def _calculate_weighted_score(
        self,
        results: list[ScorerResult],
    ) -> float:
        """Calculate weighted average of all algorithm scores.

        Args:
            results: List of ScorerResult objects

        Returns:
            Weighted average score in [0, 1]

        """
        if not results:
            return 0.0

        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(r.weighted_score for r in results)
        return weighted_sum / total_weight

    def _aggregate_component_scores(
        self,
        results: list[ScorerResult],
    ) -> dict[str, float]:
        """Aggregate component scores across all algorithms.

        Takes the average of each component across algorithms that provide it.

        Args:
            results: List of ScorerResult objects

        Returns:
            Dictionary mapping component names to average scores

        """
        component_scores: dict[str, list[float]] = {}

        # Collect scores for each component
        for result in results:
            for component, score in result.component_scores.items():
                if component not in component_scores:
                    component_scores[component] = []
                component_scores[component].append(float(score))

        # Calculate averages
        averaged = {}
        for component, scores in component_scores.items():
            if scores:
                averaged[component] = sum(scores) / len(scores)

        return averaged

    def get_top_matches(
        self,
        resumes: list[str],
        job_description: str,
        top_n: int = 10,
        **kwargs: Any,
    ) -> list[tuple[int, float, str]]:
        """Rank multiple resumes against a single job description.

        Useful for HR batch screening to find top candidates.

        Args:
            resumes: List of resume texts
            job_description: Job description to match against
            top_n: Number of top results to return
            **kwargs: Additional parameters passed to scorers

        Returns:
            List of (index, score, preview) tuples, sorted by score descending

        """
        results = []

        for idx, resume_text in enumerate(resumes):
            tournament_result = self.score(resume_text, job_description, **kwargs)
            # Create preview (first 100 chars)
            preview = resume_text[:100].replace("\n", " ").strip()
            results.append((idx, tournament_result.overall_score, preview))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_n]


# Convenience function for quick scoring
def score_resume(
    resume_text: str,
    job_description: str,
    custom_scorers: list[BaseScorer] | None = None,
) -> TournamentResult:
    """Score a resume against a job description using the tournament.

    Convenience function that creates a tournament and runs scoring.

    Args:
        resume_text: Full resume text
        job_description: Full job description text
        custom_scorers: Optional custom list of scorers

    Returns:
        TournamentResult with aggregated score

    """
    tournament = ATSTournament(scorers=custom_scorers)
    return tournament.score(resume_text, job_description)
