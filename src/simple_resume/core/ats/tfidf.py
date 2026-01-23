"""TF-IDF (Term Frequency-Inverse Document Frequency) + Cosine Similarity scorer.

This scorer uses statistical NLP to measure resume-job similarity based on:
- Term frequency (how often words appear)
- Inverse document frequency (how unique/rare words are)
- Cosine similarity (angular similarity between document vectors)

This is a fast, interpretable approach that works well for keyword matching
but misses semantic meaning (e.g., "k8s" vs "Kubernetes").
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

if TYPE_CHECKING:
    from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    EXPERIENCE_RELEVANCE_NORMALIZER,
    TOP_KEYWORDS_LIMIT,
    validate_ngram_range,
    validate_weight,
)

logger = logging.getLogger(__name__)


class TFIDFScorer(BaseScorer):
    """TF-IDF + Cosine Similarity scorer for resume-job matching.

    Uses scikit-learn's TfidfVectorizer to convert text to numerical
    vectors, then calculates cosine similarity between resume and
    job description.

    Pros:
    - Fast computation
    - Interpretable results (can inspect top keywords)
    - Good for exact keyword matching

    Cons:
    - Misses semantic meaning (synonyms treated as different words)
    - No context understanding
    - Sensitive to spelling variations
    """

    def __init__(
        self,
        weight: float = 1.0,
        max_features: int = 1000,
        ngram_range: tuple[int, int] = (1, 2),
        min_df: int = 1,
        max_df: float = 0.9,
    ) -> None:
        """Initialize TF-IDF scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            max_features: Maximum number of features (vocabulary size)
            ngram_range: Range of n-grams to consider (1, 2) = unigrams + bigrams
            min_df: Minimum document frequency for a term
            max_df: Maximum document frequency (ignore overly common terms)

        Raises:
            ValueError: If weight is outside [0, 1] or ngram_range is invalid

        """
        validate_weight(weight, "weight")
        validate_ngram_range(ngram_range, "ngram_range")
        super().__init__(weight=weight)
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
            lowercase=True,
        )

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for TF-IDF.

        Args:
            text: Raw text input

        Returns:
            Cleaned text

        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters but keep word separators
        text = re.sub(r"[^\w\s\-\.,/]", " ", text)
        return text.strip()

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score resume against job description using TF-IDF + cosine similarity.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters (unused)

        Returns:
            ScorerResult with similarity score and details

        """
        # Handle edge cases
        if not resume_text.strip() or not job_description.strip():
            return ScorerResult(
                name="tfidf_cosine",
                score=0.0,
                weight=self.weight,
                details={
                    "cosine_similarity": 0.0,
                    "top_job_keywords": [],
                    "top_resume_keywords": [],
                    "shared_keywords": [],
                    "error": "Empty input provided",
                },
            )

        # Preprocess texts
        resume_clean = self._preprocess_text(resume_text)
        job_clean = self._preprocess_text(job_description)

        # Check if preprocessing removed everything (only stopwords)
        if not resume_clean.strip() or not job_clean.strip():
            return ScorerResult(
                name="tfidf_cosine",
                score=0.0,
                weight=self.weight,
                details={
                    "cosine_similarity": 0.0,
                    "top_job_keywords": [],
                    "top_resume_keywords": [],
                    "shared_keywords": [],
                    "error": "No valid terms after preprocessing",
                },
            )

        # Create TF-IDF vectors with error handling
        # Use local vectorizer variable to avoid mutating instance state
        # This preserves functional purity of the score() method
        vectorizer = self.vectorizer
        used_fallback = False
        try:
            corpus = [resume_clean, job_clean]
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError as e:
            # Handle sklearn edge case (e.g., "no terms remain after pruning")
            # Log the specific error for debugging before falling back
            logger.warning(
                "TF-IDF vectorization failed with primary settings: %s. "
                "Falling back to permissive vectorizer.",
                str(e),
            )
            # Fallback to more permissive vectorizer (local, not stored on self)
            used_fallback = True
            vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 1),  # Use unigrams only
                min_df=1,
                max_df=1.0,
                stop_words=None,  # Don't filter stopwords
                lowercase=True,
            )
            corpus = [resume_clean, job_clean]
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
            except ValueError as fallback_error:
                # Even fallback failed - return zero similarity
                # This happens when text is empty or only contains non-word characters
                logger.warning(
                    "TF-IDF fallback vectorizer also failed: %s. "
                    "Returning zero similarity.",
                    str(fallback_error),
                )
                return ScorerResult(
                    name="tfidf_cosine",
                    score=0.0,
                    weight=self.weight,
                    details={
                        "cosine_similarity": 0.0,
                        "top_job_keywords": [],
                        "top_resume_keywords": [],
                        "shared_keywords": [],
                        "error": f"No valid terms found: {fallback_error}",
                    },
                )

        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarity_score = float(similarity_matrix[0][0])

        # Clamp to [0, 1] to handle floating-point precision issues
        similarity_score = max(0.0, min(1.0, similarity_score))

        # Extract feature names and scores for interpretability
        feature_names = vectorizer.get_feature_names_out()
        resume_tfidf = tfidf_matrix[0].toarray()[0]
        job_tfidf = tfidf_matrix[1].toarray()[0]

        # Get top keywords from job description (what they're looking for)
        job_keyword_indices = {i for i, score in enumerate(job_tfidf) if score > 0}
        top_job_keywords = [
            (feature_names[i], float(job_tfidf[i]))
            for i in sorted(
                job_keyword_indices, key=lambda x: job_tfidf[x], reverse=True
            )
        ][:TOP_KEYWORDS_LIMIT]

        # Get top keywords from resume (what they offer)
        resume_keyword_indices = {
            i for i, score in enumerate(resume_tfidf) if score > 0
        }
        top_resume_keywords = [
            (feature_names[i], float(resume_tfidf[i]))
            for i in sorted(
                resume_keyword_indices, key=lambda x: resume_tfidf[x], reverse=True
            )
        ][:TOP_KEYWORDS_LIMIT]

        # Calculate component scores for the refined rubric
        component_scores = self._calculate_component_scores(
            resume_tfidf, job_tfidf, feature_names
        )

        return ScorerResult(
            name="tfidf_cosine",
            score=similarity_score,
            weight=self.weight,
            details={
                "cosine_similarity": similarity_score,
                "top_job_keywords": top_job_keywords,
                "top_resume_keywords": top_resume_keywords,
                "shared_keywords": self._get_shared_keywords(
                    resume_tfidf, job_tfidf, feature_names
                ),
                "ngram_range": (1, 1) if used_fallback else self.ngram_range,
                "max_features": self.max_features,
                "used_fallback_vectorizer": used_fallback,
            },
            component_scores=component_scores,
        )

    def _calculate_component_scores(
        self,
        resume_tfidf: NDArray[np.floating[Any]],
        job_tfidf: NDArray[np.floating[Any]],
        feature_names: NDArray[np.str_],  # noqa: ARG002
    ) -> dict[str, float]:
        """Calculate component scores based on TF-IDF analysis.

        Args:
            resume_tfidf: TF-IDF vector for resume (numpy array)
            job_tfidf: TF-IDF vector for job description (numpy array)
            feature_names: Feature names from vectorizer (unused, for API consistency)

        Returns:
            Dictionary of component scores derived from TF-IDF vectors:
            - jaccard_similarity: Set intersection / union of non-zero term indices
            - keyword_density: Proportion of job keywords found in resume
            - experience_relevance: Weighted sum of shared TF-IDF scores, normalized

        """
        # Get non-zero indices for both documents
        resume_indices = {i for i, score in enumerate(resume_tfidf) if score > 0}
        job_indices = {i for i, score in enumerate(job_tfidf) if score > 0}

        # Jaccard similarity (intersection / union)
        intersection = resume_indices & job_indices
        union = resume_indices | job_indices
        jaccard_score = len(intersection) / len(union) if union else 0.0

        # Keyword density: proportion of job keywords found in resume
        keyword_density = len(intersection) / len(job_indices) if job_indices else 0.0

        # Experience relevance: weighted by TF-IDF scores of shared terms
        # See EXPERIENCE_RELEVANCE_NORMALIZER constant for rationale
        shared_tfidf_sum = sum(resume_tfidf[i] * job_tfidf[i] for i in intersection)
        experience_relevance = min(
            1.0, shared_tfidf_sum / EXPERIENCE_RELEVANCE_NORMALIZER
        )

        return {
            "jaccard_similarity": jaccard_score,
            "keyword_density": keyword_density,
            "experience_relevance": experience_relevance,
        }

    def _get_shared_keywords(
        self,
        resume_tfidf: NDArray[np.floating[Any]],
        job_tfidf: NDArray[np.floating[Any]],
        feature_names: NDArray[np.str_],
    ) -> list[tuple[str, float, float]]:
        """Get keywords that appear in both documents with their scores.

        Args:
            resume_tfidf: TF-IDF vector for resume (numpy array)
            job_tfidf: TF-IDF vector for job description (numpy array)
            feature_names: Feature names from vectorizer (numpy array)

        Returns:
            List of (keyword, resume_score, job_score) tuples sorted by
            combined TF-IDF score (resume_score * job_score), limited to
            TOP_KEYWORDS_LIMIT entries.

        """
        shared = []
        for i, (r_score, j_score) in enumerate(zip(resume_tfidf, job_tfidf)):
            if r_score > 0 and j_score > 0:
                shared.append((feature_names[i], float(r_score), float(j_score)))

        # Sort by combined TF-IDF score
        shared.sort(key=lambda x: x[1] * x[2], reverse=True)
        return shared[:TOP_KEYWORDS_LIMIT]
