# Similarity Algorithm Evaluation

This document evaluates alternative similarity algorithms for resume-job matching beyond the current Jaccard N-gram approach.

## Current State: Jaccard N-gram

**Location**: `src/simple_resume/core/ats/jaccard.py`

### How It Works

Jaccard N-gram measures similarity by:
1. Converting text to character n-grams (typically 3-character sequences)
2. Computing Jaccard similarity = (intersection) / (union) of n-gram sets
3. Returning score in [0, 1] range

### Strengths

- **Phrase-level matching**: Handles word order well (e.g., "machine learning" vs "learning machine")
- **Compound terms**: Correctly matches multi-word technical terms
- **No dependencies**: Pure Python, no external libraries
- **Interpretability**: Easy to explain and debug
- **Offline-first**: No network or model dependencies

### Limitations

- **Typo sensitivity**: Small typos significantly reduce score
- **Semantic blindness**: "rockstar developer" and "senior developer" score low
- **No synonym understanding**: Different words with same meaning score poorly

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Accuracy | 30% | Correctly identifies relevant matches |
| Performance | 20% | Speed of computation |
| Dependencies | 15% | External library requirements |
| Interpretability | 15% | Can explain why scores match |
| Offline Support | 10% | Works without network/API calls |
| Implementation Effort | 10% | Complexity to integrate |

## Alternative Algorithms

### 1. Levenshtein Distance (Edit Distance)

**How It Works**: Measures minimum number of single-character edits (insertions, deletions, substitutions) to transform one string into another.

**Pros**:
- Typo tolerance: "Pythn" matches "Python"
- Fuzzy matching: Handles spelling mistakes well
- Simple implementation

**Cons**:
- Computationally expensive: O(n*m) for strings of length n, m
- Word-boundary blind: "machine learning" and "learning machine" score poorly
- Poor for long text

**Best For**: Short text comparison (names, titles, individual skills)

**Verdict**: 3.5/5 - Good as supplemental scorer for short fields

### 2. MinHash with LSH (Locality-Sensitive Hashing)

**How It Works**: Approximates Jaccard similarity using hash-based signatures for efficient large-scale comparison.

**Pros**:
- Efficient for large datasets: Sub-linear query time
- Scalable: Billions of comparisons feasible
- Good approximation: ~95% of Jaccard accuracy

**Cons**:
- Overkill for single resume: Designed for batch processing
- Implementation complexity: Requires tuning parameters
- Overhead: Hash computation not worth it for <1000 documents

**Best For**: Large-scale deduplication (1000+ resumes)

**Verdict**: 2/5 - Not suited for single resume-job matching

### 3. Word2Vec / GloVe (Word Embeddings)

**How It Works**: Maps words to dense vector space where semantic similarity = geometric proximity.

**Pros**:
- Semantic understanding: "developer" ~ "engineer"
- Synonym matching: "rockstar developer" ~= "senior developer"
- Pre-trained models available

**Cons**:
- External dependencies: Requires gensim + model files (~1GB)
- Context blind: Doesn't handle phrase-level meaning
- Model age: Many pre-trained models are outdated

**Best For**: Semantic keyword matching

**Verdict**: 3/5 - Useful but BERT is superior (already implemented)

### 4. BERT Embeddings (IMPLEMENTED in v0.2.0)

**How It Works**: Uses transformer-based deep learning model for contextual semantic understanding.

**Location**: `src/simple_resume/core/ats/bert.py`

**Pros**:
- State-of-the-art accuracy: Best semantic similarity
- Contextual understanding: Handles complex phrasing
- Already implemented: Part of v0.2.0 release

**Cons**:
- Heavy dependencies: PyTorch + transformers library
- Slower: ~500ms per score vs ~10ms for Jaccard
- Resource intensive: More memory/CPU usage

**Best For**: High-stakes matching where accuracy > speed

**Verdict**: 4.5/5 - Excellent for accuracy-critical scenarios

### 5. TF-IDF Cosine Similarity (IMPLEMENTED)

**How It Works**: Measures similarity based on word frequency patterns in documents.

**Location**: `src/simple_resume/core/ats/tfidf.py`

**Pros**:
- Keyword matching: Finds shared important terms
- Fast: Efficient with sparse matrices
- Already implemented: Core part of ATS system

**Cons**:
- Bag-of-words: Ignores word order and context
- Synonym blind: "developer" != "engineer"
- Length biased: Longer documents have different baseline

**Best For**: Keyword-heavy matching (skills, technologies)

**Verdict**: 4/5 - Strong complement to Jaccard

## Comparison Matrix

| Algorithm | Accuracy | Performance | Dependencies | Interpretability | Offline | Effort | **Total** |
|-----------|:--------:|:-----------:|:------------:|:---------------:|:-------:|:-------:|:---------:|
| Jaccard (current) | 3.5 | 5 | 5 | 5 | 5 | 5 | **4.5** |
| Levenshtein | 3 | 2 | 5 | 4 | 5 | 4 | **3.5** |
| MinHash/LSH | 4 | 4 | 3 | 3 | 5 | 2 | **3.5** |
| Word2Vec/GloVe | 4 | 3 | 2 | 2 | 4 | 3 | **3.2** |
| BERT (implemented) | 5 | 2 | 2 | 2 | 5 | 2 | **3.5** |
| TF-IDF (implemented) | 4 | 5 | 5 | 4 | 5 | 5 | **4.5** |

*Weighted scores out of 5*

## Recommendations

### Current Status (v0.2.0+)

The simple-resume ATS system uses a **tournament approach** with multiple scorers:
1. **TF-IDF Cosine**: Keyword matching
2. **Jaccard N-gram**: Phrase-level matching
3. **BERT Semantic**: Contextual understanding
4. **Keyword Exact**: Direct matching

This multi-algorithm approach provides:
- **Diversity**: Different algorithms catch different types of matches
- **Robustness**: No single point of failure
- **Flexibility**: Weights can be tuned per use case

### Future Enhancements

**Add Levenshtein for short fields** (Priority: Low)
- Use for matching names, email addresses, company names
- Implement as optional scorer for specific fields
- Minimal effort, clear use case

**Keep current tournament approach** (Priority: N/A)
- Multi-algorithm scoring is already optimal
- Each algorithm has distinct strengths
- Tournament scoring mitigates individual weaknesses

### When to Add New Algorithms

Consider adding new similarity algorithms only if:
1. **Clear gap** in current scoring (no current algorithm addresses)
2. **Low dependency** cost (pure Python or minimal deps)
3. **Significant accuracy** improvement (>10% on benchmark)
4. **Offline-first** compatible (no API requirements)

## Conclusion

The current tournament-based approach with TF-IDF, Jaccard, BERT, and Keyword matching provides excellent coverage of different similarity types. Adding Levenshtein for short-field fuzzy matching would be a low-effort enhancement. Otherwise, the current algorithm set is comprehensive and well-balanced.

---
**Document Version**: 1.0
**Last Updated**: 2026-01-25
**Related Issues**: #61, #54 (BERT implementation)
