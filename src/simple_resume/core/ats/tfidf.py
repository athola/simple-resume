"""TF-IDF (Term Frequency-Inverse Document Frequency) + Cosine Similarity scorer.

This scorer uses statistical NLP to measure resume-job similarity based on:
- Term frequency (how often words appear)
- Inverse document frequency (how unique/rare words are)
- Cosine similarity (angular similarity between document vectors)

This is a fast, interpretable approach that works well for keyword matching
but misses semantic meaning (e.g., "k8s" vs "Kubernetes").
"""

from __future__ import annotations

import re
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from simple_resume.core.ats.base import BaseScorer, ScorerResult


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
            weight: Weight in tournament (default: 1.0)
            max_features: Maximum number of features (vocabulary size)
            ngram_range: Range of n-grams to consider (1, 2) = unigrams + bigrams
            min_df: Minimum document frequency for a term
            max_df: Maximum document frequency (ignore overly common terms)

        """
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
        try:
            corpus = [resume_clean, job_clean]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except ValueError:
            # Handle sklearn edge case (e.g., "no terms remain after pruning")
            # Fallback to more permissive vectorizer
            fallback_vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 1),  # Use unigrams only
                min_df=1,
                max_df=1.0,
                stop_words=None,  # Don't filter stopwords
                lowercase=True,
            )
            corpus = [resume_clean, job_clean]
            try:
                tfidf_matrix = fallback_vectorizer.fit_transform(corpus)
                self.vectorizer = fallback_vectorizer  # Update for feature access
            except ValueError:
                # Even fallback failed - return zero similarity
                # This happens when text is empty or only contains non-word characters
                return ScorerResult(
                    name="tfidf_cosine",
                    score=0.0,
                    weight=self.weight,
                    details={
                        "cosine_similarity": 0.0,
                        "top_job_keywords": [],
                        "top_resume_keywords": [],
                        "shared_keywords": [],
                        "error": "No valid terms found in either document",
                    },
                )

        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarity_score = float(similarity_matrix[0][0])

        # Clamp to [0, 1] to handle floating-point precision issues
        similarity_score = max(0.0, min(1.0, similarity_score))

        # Extract feature names and scores for interpretability
        feature_names = self.vectorizer.get_feature_names_out()
        resume_tfidf = tfidf_matrix[0].toarray()[0]
        job_tfidf = tfidf_matrix[1].toarray()[0]

        # Get top keywords from job description (what they're looking for)
        job_keyword_indices = {i for i, score in enumerate(job_tfidf) if score > 0}
        top_job_keywords = [
            (feature_names[i], float(job_tfidf[i]))
            for i in sorted(
                job_keyword_indices, key=lambda x: job_tfidf[x], reverse=True
            )
        ][:20]

        # Get top keywords from resume (what they offer)
        resume_keyword_indices = {
            i for i, score in enumerate(resume_tfidf) if score > 0
        }
        top_resume_keywords = [
            (feature_names[i], float(resume_tfidf[i]))
            for i in sorted(
                resume_keyword_indices, key=lambda x: resume_tfidf[x], reverse=True
            )
        ][:20]

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
                "ngram_range": self.ngram_range,
                "max_features": self.max_features,
            },
            component_scores=component_scores,
        )

    def _calculate_component_scores(
        self,
        resume_tfidf: list[float],
        job_tfidf: list[float],
        feature_names: list[str],
    ) -> dict[str, float]:
        """Calculate component scores based on TF-IDF analysis.

        Maps to refined rubric components:
        - experience_relevance: Keyword overlap in experience section
        - keyword_density: Overall keyword coverage
        - skill_match: Skills present in resume vs. job requirements
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
        # Heuristic: Divide by 10.0 to normalize to [0, 1]
        # Rationale: Empirically, shared TF-IDF products rarely exceed 10.0
        # even for long documents. This provides a conservative cap that prevents
        # saturation while allowing meaningful differentiation.
        shared_tfidf_sum = sum(resume_tfidf[i] * job_tfidf[i] for i in intersection)
        experience_relevance = min(1.0, shared_tfidf_sum / 10.0)  # Normalize to [0, 1]

        return {
            "jaccard_similarity": jaccard_score,
            "keyword_density": keyword_density,
            "experience_relevance": experience_relevance,
        }

    def _get_shared_keywords(
        self,
        resume_tfidf: list[float],
        job_tfidf: list[float],
        feature_names: list[str],
    ) -> list[tuple[str, float, float]]:
        """Get keywords that appear in both documents with their scores.

        Returns:
            List of (keyword, resume_score, job_score) tuples

        """
        shared = []
        for i, (r_score, j_score) in enumerate(zip(resume_tfidf, job_tfidf)):
            if r_score > 0 and j_score > 0:
                shared.append((feature_names[i], float(r_score), float(j_score)))

        # Sort by combined TF-IDF score
        shared.sort(key=lambda x: x[1] * x[2], reverse=True)
        return shared[:20]  # Top 20 shared keywords
