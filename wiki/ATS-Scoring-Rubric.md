# ATS Scoring Rubric

## Overview

The ATS (Applicant Tracking System) scoring system uses a **tournament-style approach** where multiple algorithms score resumes against job descriptions, and results are combined using a weighted rubric.

## Scoring Philosophy

### Experience-First, Balanced Approach

The rubric prioritizes **experience relevance** over keyword matching:
1. **Skills are teachable** - strong engineers can learn new technologies quickly.
2. **Experience patterns repeat** - successful projects demonstrate transferable abilities.
3. **Context matters** - "deployed microservices at scale" > "knows Kubernetes".

### Gates + Boosters

The system uses both filtering ("gates") and ranking ("boosters"):
- **Gates**: Filter out candidates lacking critical requirements.
- **Boosters**: Reward candidates exceeding expectations with bonus points.

---

## Total Score Formula (X/100)

```python
TOTAL_SCORE = (
    EXPERIENCE_SCORE * 0.35 +        # 0-35 points
    SKILL_MATCH_SCORE * 0.25 +      # 0-25 points
    SEMANTIC_SIMILARITY * 0.15 +    # 0-15 points
    KEYWORD_DENSITY_SCORE * 0.10 +  # 0-10 points
    EDUCATION_SCORE * 0.10 +        # 0-10 points
    FORMAT_COMPATIBILITY * 0.05     # 0-5 points
)
```

---

## Component Breakdown

### 1. Experience Score (35 points) - PRIMARY

#### Gates (Filters)
| Criterion | Points | Description |
|-----------|--------|-------------|
| Minimum Years Met? | 0-3 | 0=b below min, 1=meets min, 2=20% above, 3=50%+ above |
| Relevant Domain? | 0-5 | 0=no match, 2=adjacent, 5=direct match |

#### Boosters (Rewards)
| Criterion | Points | Description |
|-----------|--------|-------------|
| Years of Experience | 0-10 | Logarithmic scaling (diminishing returns after 10 years) |
| Relevance Score | 0-8 | TF-IDF/BERT semantic similarity on experience descriptions |
| Career Progression | 0-4 | Title/responsibility growth |
| Impact Indicators | 0-5 | Quantified achievements, leadership signals |

**Total Experience**: Gates (0-8) + Boosters (0-27) = **0-35 points**

---

### 2. Skill Match Score (25 points)

#### Gate
| Criterion | Points | Description |
|-----------|--------|-------------|
| Critical Skills Present? | 0-5 | All must-have skills required to pass |

#### Boosters
| Criterion | Points | Description |
|-----------|--------|-------------|
| Required Skills Coverage | 0-15 | `(matched / total) * 15` |
| Bonus Skills | 0-5 | 1 point each for relevant skills beyond requirements |

**Total Skills**: Gate (0-5) + Boosters (0-20) = **0-25 points**

---

### 3. Semantic Similarity (15 points)

- **Algorithm**: TF-IDF cosine similarity.
- **Score**: `cosine_similarity * 15`
- **Range**: 0-15 points

---

### 4. Keyword Density (10 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Required Keywords | 0-6 | TF-IDF frequency scores |
| Contextual Placement | 0-4 | Keywords in summaries/objectives > sections |

**Total Keywords**: **0-10 points**

---

### 5. Education Score (10 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Degree Match | 0-5 | Exact=5, Related=3, None=0 |
| Institution Tier | 0-2 | Tier 1=2, Tier 2=1, Other=0 |
| Achievements | 0-3 | GPA>3.5=1, Awards=1, Publications=1 |

**Total Education**: **0-10 points**

---

### 6. Format Compatibility (5 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Parse Success | 3 | Successfully extract text |
| Structure | 2 | Has standard sections |

**Total Format**: **0-5 points**

---

## Balanced Screening: Gates + Boosters

### Gate Behavior (Filtering)

```python
# Minimum thresholds to pass initial screen
MIN_SCORE = 50  # Resume must score 50+/100
MIN_EXPERIENCE_GATE = 3  # Must pass minimum experience gate
MIN_CRITICAL_SKILLS = 5  # Must have all critical skills
```

**Candidates are filtered OUT if**:
1. Total score < 50
2. Missing critical skills (gate = 0)
3. Below minimum experience years

### Booster Behavior (Ranking)

```python
# For candidates who pass gates, boosters determine rank
BOOSTER_MULTIPLIER = 1.2  # Top 10% get 20% bonus
```

**Top candidates get bonus for**:
- Exceeding requirements (e.g., 2x required years)
- Demonstrated impact (quantified achievements)
- Leadership signals

---

## Scoring Algorithms

| Algorithm | Weight | Description | Status |
|-----------|--------|-------------|--------|
| TF-IDF + Cosine | 0.40 | Statistical term frequency analysis | Implemented |
| Jaccard + N-gram | 0.30 | Set intersection and phrase overlap | Implemented |
| Exact Keyword | 0.30 | Direct keyword matching with fuzzy tolerance | Implemented |
| BERT Semantic | 0.40 | Contextual embeddings for semantic understanding | Implemented (optional) |

**Note:** BERT scorer requires the `bert` extra: `uv add simple-resume[bert]` or `pip install simple-resume[bert]`. The BERT model name can be configured via `ATSTournament(bert_model_name="...")`.

---

## Example Report

```yaml
ats_scoring_report:
  overall_score:
    total: 78.5
    percentile: "85th"

  component_scores:
    experience:
      score: 26.5
      max: 35
      weight: 0.35
      details:
        years: 5
        required_years: 3
        relevance_score: 0.85
        progression_detected: true

    skill_match:
      score: 20.0
      max: 25
      weight: 0.25
      details:
        matched_skills: ["Python", "AWS", "Docker"]
        missing_skills: ["Kubernetes", "Terraform"]

    semantic_similarity:
      score: 12.0
      max: 15
      weight: 0.15
      details:
        cosine_similarity: 0.80

    keyword_density:
      score: 8.0
      max: 10
      weight: 0.10
      details:
        required_keywords_found: 8
        required_keywords_total: 12

    education:
      score: 8.0
      max: 10
      weight: 0.10
      details:
        degree_match: "Bachelor's in CS"

    format_compatibility:
      score: 4.0
      max: 5
      weight: 0.05
      details:
        parse_success: true

  recommendations:
    top_improvements:
      - category: "skills"
        impact: "+8.5 points"
        suggestion: "Add Kubernetes and Terraform experience"
```

---

## References

- **Issue #7**: NLP resume screening capability
- **Issue #8**: Provide-your-own-key for LLM integration
- **Issue #54**: BERT semantic similarity scorer
