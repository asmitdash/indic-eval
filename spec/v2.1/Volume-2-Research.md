# IndicEval Standard (IES) v2.1 — Volume 2
## Research Benchmark Specification

**Status:** Draft v1.0
**Classification:** Normative
**Supersedes:** v2.0 Volume 2 (frozen)
**Changes from v2.0:** Indic-specific translation metric variants pinned (#17), Exact Match normalization spec added (#15). All v2.0 task weights preserved.

---

## 1. Purpose

Scientific core of IndicEval. Measures language understanding, reasoning, translation, summarization, information extraction, classification, and cross-lingual robustness for Indian languages using reproducible methods. Contributes 40% of total IndicEval score.

## 2. Design Goals

- Measure language understanding, not memorization.
- Support multilingual Indian evaluation.
- Support cross-lingual reasoning.
- Support reproducibility on public set.
- Maintain stability across releases (per V1 P3 versioning).

## 3. Supported Languages

### Tier 1 (mandatory)
| Language | Code |
|---|---|
| Hindi | hi |
| Marathi | mr |
| Bengali | bn |
| Tamil | ta |
| Telugu | te |
| Gujarati | gu |
| Kannada | kn |
| Malayalam | ml |
| Punjabi | pa |
| Odia | or |

### Tier 2 (optional in v2.1)
Assamese, Urdu, Sanskrit, Konkani, Kashmiri.

### Tier 3 (dialects, see V6 §Dialects)
Bhojpuri, Awadhi, Magahi, Haryanvi, Chhattisgarhi.

## 4. Dataset Philosophy

Diverse · Balanced · Human-reviewed · Versioned (immutable per version) · Auditable.

## 5. Dataset Composition (v2.1 sample budget)

| Type | Public | Hidden | Total |
|---|---|---|---|
| Research samples | 5,000 | 2,000 | 7,000 |

Unchanged from v2.0.

## 6. Difficulty Distribution

| Difficulty | Percentage |
|---|---|
| Easy | 25% |
| Medium | 45% |
| Hard | 25% |
| Expert | 5% |

## 7. Task Distribution

| Task | Weight |
|---|---|
| Reading Comprehension | 25% |
| Question Answering | 25% |
| Classification | 15% |
| Summarization | 15% |
| Translation | 10% |
| Information Extraction | 10% |

## 8. Reading Comprehension

Evaluates understanding. Example: a Marathi government circular; question: "What changed?"

Scoring: Exact Match 40%, F1 40%, Semantic Similarity 20%. Exact Match uses the V7 Indic normalization pipeline (#15).

## 9. Question Answering

Measures factual understanding across History, Geography, Culture, Government, Science, Education, General Knowledge. Preferred metric: Exact Match (post-normalization).

## 10. Classification

Sentiment (positive/neutral/negative); Intent (government, banking, legal, healthcare). Scoring: Accuracy.

## 11. Summarization

Sources: government circulars, news, legal documents, educational content.

| Metric | Weight |
|---|---|
| ROUGE-L | 40% |
| BERTScore | 40% |
| Compression Quality | 20% |

## 12. Translation (metric variants pinned per fix #17)

Pairs: Hindi, Marathi, Tamil, Telugu, Gujarati, Bengali — each ↔ English.

| Metric | Variant | Weight |
|---|---|---|
| BLEU | SacreBLEU 2.4.x default tokenizer + `intl` for Indic | 20% |
| chrF++ | word-order=2 (chrF++) | 30% |
| COMET | `Unbabel/wmt22-comet-da` | 30% |
| BLEURT | `BLEURT-20` (lucadiliello checkpoint) | 20% |

**Reproducibility note:** Checkpoint hashes published in `spec/v2.1/checkpoints.lock` before any score is normative. Until then, scores are advisory.

**Indic caveat:** BLEU is known to underweight Indic morphology. chrF++ and COMET-22 carry the bulk of the signal; BLEU is retained for cross-benchmark comparability only.

## 13. Information Extraction

Extract structured data. Example — GST registration notice:
```json
{
  "gst_number": "",
  "date": "",
  "entity": ""
}
```
Scoring: Precision · Recall · F1 (on field-level matches after V7 normalization).

## 14. Cross-Lingual Reasoning

Question in Hindi, context in English, answer in Marathi. Measures correctness and consistency.

## 15. Code-Mixed Evaluation (flagship)

Weight: 15% of Research Benchmark. Examples:
```
Bhai GST filing kab hai?
Mala PAN update karaycha aahe.
UPI payment reverse kasa karaycha?
```
Tests: intent understanding, context retention, language consistency, response quality.

## 16. Transliteration

Romanized → native-script understanding. Languages: Hindi, Marathi, Gujarati, Punjabi, Tamil, Telugu. Scoring: intent accuracy + semantic match (post-normalization).

## 17. Dialect Benchmark

Weight: 10% of Research. Dialects: Bhojpuri, Awadhi, Magahi, Haryanvi, Chhattisgarhi (#3 — added Chhattisgarhi to dialect list to match V6 budget). Tasks: QA, translation, intent detection.

## 18. Sample Schema

```json
{
  "id": "HI_QA_0001",
  "version": "2.1",
  "language": "Hindi",
  "task": "qa",
  "difficulty": "medium",
  "domain": "government",
  "question": "...",
  "gold_answer": "...",
  "scoring_method": "exact_match_normalized"
}
```

## 19. Dataset Metadata Schema

```json
{
  "source": "",
  "reviewer_1": "",
  "reviewer_2": "",
  "iaa_kappa": 0.0,
  "language": "",
  "domain": "",
  "created_at": "",
  "benchmark_version": "2.1"
}
```

`iaa_kappa` per fix #13 — Cohen's κ between reviewers; samples with κ < 0.7 require third-reviewer adjudication.

## 20. Hidden Dataset Governance

Hidden set: never published, never in Git, never in reports. Minimum size: 25%. Audit Committee certifies hidden-set scores per V1 §11.

## 21. Public Dataset Governance

Public set: downloadable, reproducible, documented.

## 22. Scoring Formula — Research

```
Research = Reading × 0.25
        + QA × 0.25
        + Classification × 0.15
        + Summarization × 0.15
        + Translation × 0.10
        + Information Extraction × 0.10
```
Normalized to 0–100. Each sub-score is also floored at 0 (per V7 fix #6) so bad runs don't propagate negatives.

## 23. Statistical Validation

Minimum confidence: 95%. Paired bootstrap (10,000 iterations) per fix #14. Confidence intervals reported alongside every published score.

## 24. Integrity Tests

- Dataset duplication test (≤1% overlap with prior versions).
- Translation leakage test (no source-target pairs from public training corpora).
- Label leakage test.
- Cross-language consistency test.
- Hidden set validation (Audit Committee).

## 25. Success Criteria

- Reproducible scores on public set.
- Hidden set uncompromised.
- Stable confidence intervals.
- Balanced language coverage.
- Dataset quality passes audit (κ ≥ 0.7 per language-domain pair).

## 26. Deliverables

Research score, language scores, domain scores, task scores, confidence intervals, error analysis, failure-registry entries.
