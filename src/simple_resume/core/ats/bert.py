"""BERT semantic similarity scorer using sentence-transformers.

Uses pre-trained transformer models to generate contextual embeddings
for resume and job description text, then calculates cosine similarity.

Key advantages over TF-IDF:
- Understands synonyms and paraphrases (k8s ≈ Kubernetes)
- Captures contextual meaning (deployed microservices ≈ built distributed systems)
- Better handling of varied terminology for same concepts
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import validate_weight

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _import_sentence_transformer() -> Any:
    """Import SentenceTransformer class from sentence-transformers package.

    This is a module-level helper to centralize the lazy import of the
    heavy sentence-transformers dependency, avoiding scattered in-function
    imports throughout the codebase.

    Returns:
        The SentenceTransformer class (typed as Any since it's an optional dep)

    Raises:
        ImportError: If sentence-transformers is not installed

    """
    from sentence_transformers import SentenceTransformer  # ty: ignore

    return SentenceTransformer


logger = logging.getLogger(__name__)

# Default model - lightweight, fast, good quality
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Environment variable for custom model selection
MODEL_ENV_VAR = "SIMPLE_RESUME_BERT_MODEL"

# Section splitting constants
MIN_SECTION_LENGTH = 20  # Minimum characters for a valid section
MAX_SECTIONS = 10  # Maximum sections to embed (prevents too many embeddings)
REQUIREMENTS_COVERAGE_THRESHOLD = 0.5  # Similarity threshold for "covered"


class BERTModelUnavailableError(Exception):
    """Raised when BERT model cannot be loaded."""

    pass


def _check_sentence_transformers_available() -> bool:
    """Check if sentence-transformers is installed.

    Uses importlib.util.find_spec to check package availability without
    actually importing it (avoids loading heavy ML dependencies).
    """
    import importlib.util

    return importlib.util.find_spec("sentence_transformers") is not None


# Cache up to 4 different models to support different use cases:
# - Default lightweight model (all-MiniLM-L6-v2): ~80MB, fast
# - High-accuracy model (all-mpnet-base-v2): ~420MB, more accurate
# - Multilingual model (paraphrase-multilingual-MiniLM-L12-v2): ~470MB
# - User-specified custom model via SIMPLE_RESUME_BERT_MODEL env var
#
# Memory footprint: ~100-500MB per model, max ~2GB with full cache.
# Models are lazily loaded on first use and cached for subsequent calls.
# See GitHub Issue #74 for rationale.
@lru_cache(maxsize=4)
def _load_model(model_name: str) -> Any:
    """Load and cache a sentence-transformers model.

    Models are cached using LRU eviction with maxsize=4 to support
    switching between different models (lightweight/accurate/multilingual)
    without reloading. Typical memory usage is 100-500MB per model.

    Args:
        model_name: HuggingFace model name or path

    Returns:
        SentenceTransformer model instance

    Raises:
        BERTModelUnavailableError: If model cannot be loaded

    """
    try:
        sentence_transformer_cls = _import_sentence_transformer()
        logger.info("Loading BERT model: %s", model_name)
        model = sentence_transformer_cls(model_name)
        logger.info("BERT model loaded successfully")
        return model
    except ImportError as e:
        msg = (
            "sentence-transformers not installed. "
            "Install with: pip install 'simple-resume[bert]'"
        )
        raise BERTModelUnavailableError(msg) from e
    except Exception as e:
        msg = f"Failed to load BERT model '{model_name}': {e}"
        raise BERTModelUnavailableError(msg) from e


class BERTScorer(BaseScorer):
    """BERT semantic similarity scorer using sentence-transformers.

    Generates contextual embeddings for resume and job description,
    then calculates cosine similarity between embeddings.

    Pros:
    - Understands semantic meaning and synonyms
    - Captures context (same word has different meanings in different contexts)
    - Handles paraphrases and rephrasing

    Cons:
    - Requires GPU for fast inference (CPU is 5-10x slower)
    - Larger memory footprint than TF-IDF
    - Model download required on first use (~80MB for default model)

    Attributes:
        model_name: Name of the sentence-transformers model to use
        available: Whether the model is available and loaded

    """

    def __init__(
        self,
        weight: float = 1.0,
        model_name: str | None = None,
    ) -> None:
        """Initialize BERT scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            model_name: HuggingFace model name. Defaults to all-MiniLM-L6-v2
                        or SIMPLE_RESUME_BERT_MODEL env var if set.

        Raises:
            ValueError: If weight is outside [0, 1]

        """
        validate_weight(weight, "weight")
        super().__init__(weight=weight)

        # Model name priority: argument > env var > default
        self.model_name = model_name or os.environ.get(MODEL_ENV_VAR) or DEFAULT_MODEL

        self._model: Any = None
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        """Check if BERT model is available and can be loaded."""
        if self._available is None:
            if not _check_sentence_transformers_available():
                self._available = False
            else:
                try:
                    self._ensure_model_loaded()
                    self._available = True
                except BERTModelUnavailableError as e:
                    logger.debug("BERT model unavailable: %s", e)
                    self._available = False
        return self._available

    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded, raising if unavailable."""
        if self._model is None:
            self._model = _load_model(self.model_name)

    def _get_embedding(self, text: str) -> NDArray[np.floating[Any]]:
        """Get embedding for a text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array

        """
        self._ensure_model_loaded()
        # Encode returns numpy array by default
        embedding: NDArray[np.floating[Any]] = self._model.encode(
            text, convert_to_numpy=True
        )
        return embedding

    def _cosine_similarity(
        self,
        vec1: NDArray[np.floating[Any]],
        vec2: NDArray[np.floating[Any]],
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity in [0, 1] (clamped from [-1, 1])

        """
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))
        # Clamp to [0, 1] - negative similarities indicate opposite meanings
        # For resume matching, we treat "opposite" as "not matching" (0)
        return max(0.0, min(1.0, similarity))

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score resume against job description using BERT embeddings.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters (unused)

        Returns:
            ScorerResult with semantic similarity score and details

        """
        # Handle unavailable model
        if not self.available:
            logger.warning(
                "BERT model unavailable. Returning zero score. "
                "Install sentence-transformers for semantic matching."
            )
            return ScorerResult(
                name="bert_semantic",
                score=0.0,
                weight=self.weight,
                details={
                    "error": "BERT model unavailable",
                    "model_name": self.model_name,
                },
            )

        # Handle empty inputs
        if not resume_text.strip() or not job_description.strip():
            logger.debug(
                "BERT scorer received empty input - resume: %d chars, job: %d chars",
                len(resume_text),
                len(job_description),
            )
            return ScorerResult(
                name="bert_semantic",
                score=0.0,
                weight=self.weight,
                details={
                    "error": "Empty input provided",
                    "model_name": self.model_name,
                },
            )

        # Generate embeddings
        try:
            resume_embedding = self._get_embedding(resume_text)
            job_embedding = self._get_embedding(job_description)
        except Exception as e:
            logger.exception("Failed to generate BERT embeddings")
            return ScorerResult(
                name="bert_semantic",
                score=0.0,
                weight=self.weight,
                details={
                    "error": f"Embedding generation failed: {e}",
                    "model_name": self.model_name,
                },
            )

        # Calculate overall similarity
        overall_similarity = self._cosine_similarity(resume_embedding, job_embedding)

        # Calculate section-level similarities for component breakdown
        component_scores = self._calculate_section_similarities(
            resume_text, job_description
        )

        return ScorerResult(
            name="bert_semantic",
            score=overall_similarity,
            weight=self.weight,
            details={
                "semantic_similarity": overall_similarity,
                "model_name": self.model_name,
                "embedding_dimensions": len(resume_embedding),
            },
            component_scores=component_scores,
        )

    def _calculate_section_similarities(
        self,
        resume_text: str,
        job_description: str,
    ) -> dict[str, float]:
        """Calculate section-level semantic similarities.

        Splits text into sections and computes pairwise similarities
        for more granular component breakdown.

        Args:
            resume_text: Full resume text
            job_description: Full job description text

        Returns:
            Dictionary of component similarity scores

        """
        # Split job description into requirement sections
        # Simple heuristic: split by double newlines or bullet sections
        job_sections = self._split_into_sections(job_description)
        resume_sections = self._split_into_sections(resume_text)

        if not job_sections or not resume_sections:
            return {}

        # Embed all sections
        try:
            job_embeddings = [self._get_embedding(s) for s in job_sections]
            resume_embeddings = [self._get_embedding(s) for s in resume_sections]
        except (ValueError, RuntimeError) as e:
            logger.warning(
                "Failed to generate embeddings for section-level scoring: %s. "
                "Returning component scores from overall similarity only.",
                e,
            )
            return {}
        except Exception as e:
            logger.error(
                "Unexpected error generating section embeddings: %s. "
                "Returning component scores from overall similarity only.",
                e,
                exc_info=True,
            )
            return {}

        # Calculate best match for each job section
        section_scores = []
        for job_emb in job_embeddings:
            best_match = max(
                self._cosine_similarity(job_emb, res_emb)
                for res_emb in resume_embeddings
            )
            section_scores.append(best_match)

        # Aggregate into component scores
        if not section_scores:
            return {}

        return {
            "skills_semantic": float(np.mean(section_scores)),
            "experience_semantic": float(np.median(section_scores)),
            "requirements_coverage": float(
                sum(1 for s in section_scores if s > REQUIREMENTS_COVERAGE_THRESHOLD)
                / len(section_scores)
            ),
        }

    def _split_into_sections(self, text: str) -> list[str]:
        """Split text into meaningful sections.

        Args:
            text: Full text to split

        Returns:
            List of section strings (non-empty)

        """
        # Split by double newlines or bullet-heavy sections
        sections = re.split(r"\n\n+|\n(?=[•\-\*]\s)", text)

        # Filter empty and very short sections
        sections = [s.strip() for s in sections if len(s.strip()) > MIN_SECTION_LENGTH]

        # Limit to prevent too many embeddings
        return sections[:MAX_SECTIONS]
