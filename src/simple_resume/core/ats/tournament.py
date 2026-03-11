"""Tournament runner for multi-algorithm ATS scoring.

Runs multiple scoring algorithms sequentially and aggregates results
using weighted averages to produce a comprehensive resume-job match score.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    DEFAULT_BERT_WEIGHT,
    DEFAULT_JACCARD_WEIGHT,
    DEFAULT_KEYWORD_WEIGHT,
    DEFAULT_PREVIEW_LENGTH,
    DEFAULT_TFIDF_WEIGHT,
    FALLBACK_JACCARD_WEIGHT,
    FALLBACK_KEYWORD_WEIGHT,
    FALLBACK_TFIDF_WEIGHT,
    HUMAN_BERT_WEIGHT,
    HUMAN_FALLBACK_JACCARD_WEIGHT,
    HUMAN_FALLBACK_KEYWORD_WEIGHT,
    HUMAN_FALLBACK_TFIDF_WEIGHT,
    HUMAN_JACCARD_WEIGHT,
    HUMAN_KEYWORD_WEIGHT,
    HUMAN_TFIDF_WEIGHT,
    ScoringMode,
    validate_score,
)
from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer, KeywordScorerConfig
from simple_resume.core.ats.tfidf import TFIDFScorer

logger = logging.getLogger(__name__)


def _import_bert_scorer() -> Any:
    """Import BERTScorer class from the bert module.

    This is a module-level helper to centralize the lazy import of the
    BERTScorer class, which has heavy dependencies (sentence-transformers).
    Keeps the import at module level while still being lazy-evaluated.

    Returns:
        The BERTScorer class (typed as Any since it's lazily imported)

    Raises:
        ImportError: If the bert module or its dependencies are unavailable

    """
    from simple_resume.core.ats.bert import BERTScorer

    return BERTScorer


@dataclass
class TournamentResult:
    """Result from running multiple scoring algorithms.

    Attributes:
        overall_score: Final weighted average score (must be in [0, 1])
        algorithm_results: Results from each individual algorithm
        component_breakdown: Scores by rubric component (all values in [0, 1])
        metadata: Additional tournament metadata
        failed_scorers: List of (scorer_name, error_message) for scorers that failed

    Raises:
        ValueError: If overall_score or component_breakdown values are outside [0, 1]

    """

    overall_score: float
    algorithm_results: list[ScorerResult] = field(default_factory=list)
    component_breakdown: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    failed_scorers: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate overall_score and component_breakdown are in valid ranges."""
        validate_score(self.overall_score, "overall_score")

        # Validate all component scores
        for key, value in self.component_breakdown.items():
            validate_score(value, f"component_breakdown[{key!r}]")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "algorithm_results": [r.to_dict() for r in self.algorithm_results],
            "component_breakdown": self.component_breakdown,
            "metadata": self.metadata,
            "failed_scorers": self.failed_scorers,
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
        include_bert: bool = True,
        bert_model_name: str | None = None,
        scoring_mode: ScoringMode = ScoringMode.ATS,
    ) -> None:
        """Initialize the tournament with a list of scorers.

        Args:
            scorers: List of scoring algorithms to use. If None, uses default set.
            include_bert: Whether to include BERT scorer if available (default: True).
                         Set to False to skip BERT even when sentence-transformers
                         is installed (useful for faster scoring or testing).
            bert_model_name: Override the BERT model name. Shell layer can resolve
                            this from environment variables or config files.
            scoring_mode: Weight preset to use (default: ATS).

        """
        self._bert_model_name = bert_model_name
        self._scoring_mode = scoring_mode
        if scorers is None:
            self.scorers = self._create_default_scorers(include_bert=include_bert)
        else:
            self.scorers = scorers

    def _create_default_scorers(self, include_bert: bool = True) -> list[BaseScorer]:
        """Create default scorers with appropriate weights.

        If BERT is available and enabled, uses semantic-aware weights.
        If BERT is unavailable, uses fallback statistical-only weights.
        Weights are selected based on the active scoring mode.

        Args:
            include_bert: Whether to try including BERT scorer

        Returns:
            List of configured scorers

        """
        scorers: list[BaseScorer] = []
        is_human = self._scoring_mode == ScoringMode.HUMAN_REVIEWER

        # Try to include BERT scorer if enabled
        bert_available = False
        if include_bert:
            try:
                bert_scorer_cls = _import_bert_scorer()
                bert_weight = HUMAN_BERT_WEIGHT if is_human else DEFAULT_BERT_WEIGHT
                bert_scorer = bert_scorer_cls(
                    weight=bert_weight,
                    model_name=self._bert_model_name,
                )
                if bert_scorer.available:
                    scorers.append(bert_scorer)
                    bert_available = True
                    logger.info(
                        "BERT scorer enabled with weight %.2f",
                        bert_weight,
                    )
                else:
                    logger.info(
                        "BERT scorer not available "
                        "(sentence-transformers not installed)"
                    )
            except ImportError:
                logger.info("BERT module not available")

        # Select weights based on mode and BERT availability
        if bert_available:
            tfidf_w = HUMAN_TFIDF_WEIGHT if is_human else DEFAULT_TFIDF_WEIGHT
            jaccard_w = HUMAN_JACCARD_WEIGHT if is_human else DEFAULT_JACCARD_WEIGHT
            keyword_w = HUMAN_KEYWORD_WEIGHT if is_human else DEFAULT_KEYWORD_WEIGHT
        else:
            tfidf_w = HUMAN_FALLBACK_TFIDF_WEIGHT if is_human else FALLBACK_TFIDF_WEIGHT
            jaccard_w = (
                HUMAN_FALLBACK_JACCARD_WEIGHT if is_human else FALLBACK_JACCARD_WEIGHT
            )
            keyword_w = (
                HUMAN_FALLBACK_KEYWORD_WEIGHT if is_human else FALLBACK_KEYWORD_WEIGHT
            )

        # Build keyword scorer with creative expansion for human mode
        keyword_config = KeywordScorerConfig(
            enable_creative_expansion=is_human,
        )

        scorers.extend(
            [
                TFIDFScorer(weight=tfidf_w),
                JaccardScorer(weight=jaccard_w),
                KeywordScorer(weight=keyword_w, config=keyword_config),
            ]
        )

        return scorers

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
        if error := self._validate_inputs(resume_text, job_description):
            return TournamentResult(
                overall_score=0.0,
                algorithm_results=[],
                component_breakdown={},
                metadata={"error": error},
            )

        algorithm_results, failed_scorers = self._execute_scorers(
            resume_text, job_description, **kwargs
        )

        if not algorithm_results:
            return self._all_failed_result(failed_scorers)

        return self._build_result(algorithm_results, failed_scorers)

    @staticmethod
    def _validate_inputs(resume_text: str, job_description: str) -> str | None:
        """Return error message if inputs are invalid, else None."""
        if not resume_text or not resume_text.strip():
            return "Resume text is empty"
        if not job_description or not job_description.strip():
            return "Job description is empty"
        return None

    def _execute_scorers(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> tuple[list[ScorerResult], list[tuple[str, str]]]:
        """Run all scorers and collect results and failures."""
        algorithm_results: list[ScorerResult] = []
        failed_scorers: list[tuple[str, str]] = []

        for scorer in self.scorers:
            result = self._run_scorer(
                scorer, resume_text, job_description, failed_scorers, **kwargs
            )
            if result is not None:
                algorithm_results.append(result)

        return algorithm_results, failed_scorers

    def _all_failed_result(
        self, failed_scorers: list[tuple[str, str]]
    ) -> TournamentResult:
        """Build result when all scorers failed."""
        logger.error(
            "All %d scorers failed during tournament. No score available.",
            len(self.scorers),
        )
        return TournamentResult(
            overall_score=0.0,
            algorithm_results=[],
            component_breakdown={},
            metadata={
                "error": "All scorers failed",
                "num_algorithms": len(self.scorers),
            },
            failed_scorers=failed_scorers,
        )

    def _build_result(
        self,
        algorithm_results: list[ScorerResult],
        failed_scorers: list[tuple[str, str]],
    ) -> TournamentResult:
        """Aggregate successful results into a TournamentResult."""
        return TournamentResult(
            overall_score=self._calculate_weighted_score(algorithm_results),
            algorithm_results=algorithm_results,
            component_breakdown=self._aggregate_component_scores(algorithm_results),
            metadata={
                "num_algorithms": len(self.scorers),
                "num_successful": len(algorithm_results),
                "num_failed": len(failed_scorers),
                "scorer_names": [r.name for r in algorithm_results],
                "individual_scores": [r.score for r in algorithm_results],
            },
            failed_scorers=failed_scorers,
        )

    def _run_scorer(
        self,
        scorer: BaseScorer,
        resume_text: str,
        job_description: str,
        failed_scorers: list[tuple[str, str]],
        **kwargs: Any,
    ) -> ScorerResult | None:
        """Run a single scorer with graceful error handling.

        Returns:
            ScorerResult on success, None if the scorer failed.

        """
        scorer_name = scorer.__class__.__name__
        try:
            return scorer.score(resume_text, job_description, **kwargs)
        except (ValueError, RuntimeError) as e:
            logger.warning(
                "Scorer %s failed during tournament: %s. "
                "Continuing with remaining scorers.",
                scorer_name,
                str(e),
            )
            failed_scorers.append((scorer_name, str(e)))
            return None
        except Exception as e:
            logger.error(
                "Unexpected error in scorer %s during tournament: %s. "
                "Continuing with remaining scorers.",
                scorer_name,
                str(e),
                exc_info=True,
            )
            failed_scorers.append((scorer_name, f"Unexpected error: {e}"))
            return None

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
        preview_length: int = DEFAULT_PREVIEW_LENGTH,
        **kwargs: Any,
    ) -> list[tuple[int, float, str]]:
        """Rank multiple resumes against a single job description.

        Useful for HR batch screening to find top candidates.

        Args:
            resumes: List of resume texts
            job_description: Job description to match against
            top_n: Number of top results to return
            preview_length: Length of resume preview text (default: 100 chars)
            **kwargs: Additional parameters passed to scorers

        Returns:
            List of (index, score, preview) tuples, sorted by score descending

        """
        results = []

        for idx, resume_text in enumerate(resumes):
            tournament_result = self.score(resume_text, job_description, **kwargs)
            preview = resume_text[:preview_length].replace("\n", " ").strip()
            results.append((idx, tournament_result.overall_score, preview))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_n]


# Convenience function for quick scoring
def score_resume(
    resume_text: str,
    job_description: str,
    custom_scorers: list[BaseScorer] | None = None,
    *,
    percentage: bool = True,
) -> TournamentResult:
    """Score a resume against a job description using the tournament.

    Convenience function that creates a tournament and runs scoring.

    Args:
        resume_text: Full resume text
        job_description: Full job description text
        custom_scorers: Optional custom list of scorers
        percentage: If True (default), return score as 0-100 percentage.
                   If False, return raw 0-1 score.

    Returns:
        TournamentResult with aggregated score (0-100 if percentage=True)

    """
    tournament = ATSTournament(scorers=custom_scorers)
    result = tournament.score(resume_text, job_description)

    if percentage:
        # Add percentage info to metadata (score stays 0-1 for validation)
        result.metadata["percentage_score"] = min(100.0, result.overall_score * 100)
        result.metadata["scale"] = "percentage"

    return result
