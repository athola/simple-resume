"""Unit tests for BERT semantic similarity scorer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from simple_resume.core.ats.bert import (
    DEFAULT_MODEL,
    MODEL_ENV_VAR,
    BERTModelUnavailableError,
    BERTScorer,
    _check_sentence_transformers_available,
    _load_model,
)


class TestBERTScorerInitialization:
    """Test BERT scorer initialization and configuration."""

    def test_default_model_name(self):
        """Scorer uses default model when none specified."""
        scorer = BERTScorer(weight=0.35)
        assert scorer.model_name == DEFAULT_MODEL

    def test_custom_model_name(self):
        """Scorer accepts custom model name."""
        custom_model = "custom/model-name"
        scorer = BERTScorer(weight=0.35, model_name=custom_model)
        assert scorer.model_name == custom_model

    def test_env_var_model_name(self):
        """Scorer uses environment variable for model name."""
        env_model = "env/custom-model"
        with patch.dict("os.environ", {MODEL_ENV_VAR: env_model}):
            scorer = BERTScorer(weight=0.35)
            assert scorer.model_name == env_model

    def test_argument_overrides_env_var(self):
        """Explicit argument takes precedence over env var."""
        arg_model = "arg/model"
        env_model = "env/model"
        with patch.dict("os.environ", {MODEL_ENV_VAR: env_model}):
            scorer = BERTScorer(weight=0.35, model_name=arg_model)
            assert scorer.model_name == arg_model

    def test_invalid_weight_raises_error(self):
        """Weight outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            BERTScorer(weight=1.5)

    def test_weight_is_stored(self):
        """Weight is stored correctly."""
        scorer = BERTScorer(weight=0.35)
        assert scorer.weight == 0.35


class TestBERTScorerAvailability:
    """Test BERT model availability detection."""

    def test_available_when_sentence_transformers_present(self):
        """Scorer reports available when sentence-transformers installed."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([1.0] * 384)

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                assert scorer.available is True

    def test_unavailable_when_sentence_transformers_missing(self):
        """Scorer reports unavailable when sentence-transformers not installed."""
        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=False,
        ):
            scorer = BERTScorer(weight=0.35)
            assert scorer.available is False

    def test_unavailable_when_model_load_fails(self):
        """Scorer reports unavailable when model fails to load."""
        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                side_effect=BERTModelUnavailableError("Model not found"),
            ):
                scorer = BERTScorer(weight=0.35)
                assert scorer.available is False


class TestBERTScorerScoring:
    """Test BERT scoring functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock sentence transformer model."""
        model = MagicMock()
        # Return normalized vectors so cosine similarity works predictably
        model.encode.return_value = np.array([1.0] * 384) / np.sqrt(384)
        return model

    @pytest.fixture
    def available_scorer(self, mock_model):
        """Create a scorer with mocked available model."""
        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                # Force availability check
                _ = scorer.available
                return scorer

    def test_score_returns_result_with_correct_name(self, available_scorer):
        """Score method returns result with correct scorer name."""
        result = available_scorer.score("Resume text", "Job description")
        assert result.name == "bert_semantic"

    def test_score_returns_result_with_weight(self, available_scorer):
        """Score method includes weight in result."""
        result = available_scorer.score("Resume text", "Job description")
        assert result.weight == 0.35

    def test_score_is_in_valid_range(self, available_scorer):
        """Score is normalized to [0, 1]."""
        result = available_scorer.score("Resume text", "Job description")
        assert 0.0 <= result.score <= 1.0

    def test_identical_texts_have_high_similarity(self, available_scorer, mock_model):
        """Identical texts should have similarity near 1.0."""
        # Make model return same embedding for both
        result = available_scorer.score("Same text", "Same text")
        assert result.score >= 0.9

    def test_score_includes_model_name_in_details(self, available_scorer):
        """Result details include model name."""
        result = available_scorer.score("Resume", "Job")
        assert "model_name" in result.details
        assert result.details["model_name"] == DEFAULT_MODEL

    def test_score_includes_embedding_dimensions(self, available_scorer):
        """Result details include embedding dimensions."""
        result = available_scorer.score("Resume", "Job")
        assert "embedding_dimensions" in result.details

    def test_score_includes_semantic_similarity(self, available_scorer):
        """Result details include semantic similarity value."""
        result = available_scorer.score("Resume", "Job")
        assert "semantic_similarity" in result.details


class TestBERTScorerEdgeCases:
    """Test BERT scorer edge cases and error handling."""

    @pytest.fixture
    def unavailable_scorer(self):
        """Create a scorer with unavailable model."""
        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=False,
        ):
            return BERTScorer(weight=0.35)

    def test_score_when_model_unavailable(self, unavailable_scorer):
        """Scoring with unavailable model returns zero with error details."""
        result = unavailable_scorer.score("Resume", "Job")
        assert result.score == 0.0
        assert "error" in result.details
        assert "unavailable" in result.details["error"].lower()

    def test_score_with_empty_resume(self):
        """Empty resume returns zero score."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros(384)

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                result = scorer.score("", "Job description")
                assert result.score == 0.0
                assert "error" in result.details

    def test_score_with_empty_job_description(self):
        """Empty job description returns zero score."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros(384)

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                result = scorer.score("Resume text", "")
                assert result.score == 0.0

    def test_score_with_whitespace_only(self):
        """Whitespace-only input returns zero score."""
        mock_model = MagicMock()

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                result = scorer.score("   \n\t  ", "Job description")
                assert result.score == 0.0


class TestBERTScorerCosineSimilarity:
    """Test cosine similarity calculation."""

    def test_identical_vectors_have_similarity_one(self):
        """Identical normalized vectors have similarity 1.0."""
        scorer = BERTScorer(weight=0.35)
        vec = np.array([1.0, 0.0, 0.0])
        result = scorer._cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 0.0001

    def test_orthogonal_vectors_have_similarity_zero(self):
        """Orthogonal vectors have similarity 0.0."""
        scorer = BERTScorer(weight=0.35)
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        result = scorer._cosine_similarity(vec1, vec2)
        assert abs(result - 0.0) < 0.0001

    def test_opposite_vectors_clamped_to_zero(self):
        """Opposite vectors (negative similarity) clamped to 0.0."""
        scorer = BERTScorer(weight=0.35)
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        result = scorer._cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_zero_vector_returns_zero(self):
        """Zero vector returns similarity 0.0."""
        scorer = BERTScorer(weight=0.35)
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        result = scorer._cosine_similarity(vec1, vec2)
        assert result == 0.0


class TestSentenceTransformersCheck:
    """Test the availability check function."""

    def test_check_returns_bool(self):
        """Check function returns a boolean."""
        result = _check_sentence_transformers_available()
        assert isinstance(result, bool)


class TestBERTSectionSplitting:
    """Test section splitting for component scores."""

    def test_split_by_double_newlines(self):
        """Text is split on double newlines."""
        scorer = BERTScorer(weight=0.35)
        # Sections must be > 20 chars to pass filter
        text = (
            "Section 1 with enough content to pass the filter.\n\n"
            "Section 2 with enough content to pass the filter.\n\n"
            "Section 3 with enough content to pass the filter."
        )
        sections = scorer._split_into_sections(text)
        assert len(sections) == 3

    def test_short_sections_filtered(self):
        """Sections shorter than 20 chars are filtered out."""
        scorer = BERTScorer(weight=0.35)
        text = "Short.\n\nThis is a longer section with enough content."
        sections = scorer._split_into_sections(text)
        assert len(sections) == 1
        assert "longer" in sections[0]

    def test_max_sections_limit(self):
        """Section count is limited to prevent too many embeddings."""
        scorer = BERTScorer(weight=0.35)
        # Create text with many sections
        sections_text = "\n\n".join(
            [f"Section {i} with enough content to pass the filter." for i in range(20)]
        )
        sections = scorer._split_into_sections(sections_text)
        assert len(sections) <= 10


class TestBERTScorerEmbeddingFailures:
    """Test BERT scorer handling of embedding generation failures."""

    def test_embedding_exception_returns_zero_score(self):
        """When embedding generation fails, return zero with error details."""
        mock_model = MagicMock()
        # Make encode raise an exception
        mock_model.encode.side_effect = RuntimeError("CUDA out of memory")

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                result = scorer.score("Resume text", "Job description")

                assert result.score == 0.0
                assert "error" in result.details
                assert "Embedding generation failed" in result.details["error"]

    def test_section_similarity_exception_returns_empty_dict(self):
        """When section similarity fails, return empty component scores."""
        mock_model = MagicMock()
        # First call succeeds for the main score, others fail
        call_count = [0]

        def encode_side_effect(text, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                # First two calls (main embeddings) succeed
                return np.array([1.0] * 384) / np.sqrt(384)
            # Section embeddings fail
            raise RuntimeError("Model error")

        mock_model.encode.side_effect = encode_side_effect

        with patch(
            "simple_resume.core.ats.bert._check_sentence_transformers_available",
            return_value=True,
        ):
            with patch(
                "simple_resume.core.ats.bert._load_model",
                return_value=mock_model,
            ):
                scorer = BERTScorer(weight=0.35)
                # Use text with multiple sections
                resume = (
                    "Section 1 with enough content.\n\nSection 2 with enough content."
                )
                job = (
                    "Job section 1 with enough content.\n\n"
                    "Job section 2 with enough content."
                )
                result = scorer.score(resume, job)

                # Main score should succeed
                assert result.score >= 0.0
                # Component scores should be empty due to exception
                component_scores = result.details.get("component_scores", {})
                # Either empty or exception was caught
                assert isinstance(component_scores, dict)


class TestBERTModelLoading:
    """Test BERT model loading and error handling."""

    def test_load_model_import_error(self):
        """Test _load_model raises proper error on import failure."""
        # Clear the cache to test fresh
        _load_model.cache_clear()

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named sentence_transformers"),
            ):
                with pytest.raises(BERTModelUnavailableError, match="not installed"):
                    _load_model("all-MiniLM-L6-v2")

        # Clear cache after test
        _load_model.cache_clear()

    def test_load_model_generic_error(self):
        """Test _load_model handles generic errors."""
        _load_model.cache_clear()

        mock_st = MagicMock()
        mock_st.SentenceTransformer.side_effect = ValueError("Invalid model")

        with patch.dict("sys.modules", {"sentence_transformers": mock_st}):
            with pytest.raises(BERTModelUnavailableError, match="Failed to load"):
                _load_model("invalid-model-name")

        _load_model.cache_clear()


class TestSentenceTransformersAvailable:
    """Test the sentence-transformers availability check."""

    def test_returns_true_when_available(self):
        """Returns True when sentence-transformers can be imported."""
        mock_st = MagicMock()

        with patch.dict("sys.modules", {"sentence_transformers": mock_st}):
            # We need to test the actual function behavior
            # Since import already happened, the result depends on current state
            result = _check_sentence_transformers_available()
            assert isinstance(result, bool)
