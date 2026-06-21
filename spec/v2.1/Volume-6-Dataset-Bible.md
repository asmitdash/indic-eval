# IndicEval Standard (IES) v2.1 — Volume 6
## Dataset Bible

**Status:** Draft v1.0
**Classification:** Normative
**Supersedes:** v2.0 Volume 6 (frozen)
**Changes from v2.0:**
- Master sample budget reconciled (#1, #2, #3): totals now sum correctly across all categories.
- Dialect line item added (#3).
- Reliability split into named sub-budgets (#2).
- IAA / Cohen's κ requirement added (#13).
- FDR reframed as dataset-quality metric, not "most important" model-scoring metric (#8).
- Pilot-first directive added (#18, #19).
- Versioning rule explicit (#12) — refresh = new version.

---

## 1. Purpose

The Dataset Bible is the most important document in IndicEval.

Not the code. Not the leaderboard. Not the architecture.

The dataset determines whether IndicEval becomes a useful benchmark — or leaderboard theater.

## 2. Dataset Design Principles

Every sample SHALL satisfy:

- **Relevance** — reflect a real Indian use case.
- **Difficulty** — differentiate weak and strong models.
- **Diversity** — avoid repetitive patterns.
- **Auditability** — traceable origin, two human reviewers, κ ≥ 0.7.
- **Stability** — remain valid for years (within version).
- **Non-Gamability** — difficult to memorize.

## 3. Master Dataset Structure (reconciled per #1, #2, #3)

| Category | Public | Hidden | Total |
|---|---|---|---|
| Research | 5,000 | 2,000 | 7,000 |
| Industry | 7,500 | 5,000 | 12,500 |
| Reliability — core | 1,500 | 1,000 | 2,500 |
| Reliability — hallucination | 900 | 600 | 1,500 |
| Reliability — adversarial | 900 | 600 | 1,500 |
| Reliability — dialects (5 dialects × 500) | 1,500 | 1,000 | 2,500 |
| Safety | 1,500 | 1,000 | 2,500 |
| Quality | 600 | 400 | 1,000 |
| **Total v2.1** | **19,400** | **11,600** | **31,000** |

**v2.1 initial dataset target:** ~31,000 samples (up from v2.0's claimed 24,000+ which didn't sum).
**v3 target:** 100,000+.

**Hidden ratio:** 11,600 / 31,000 ≈ 37% (V1 §10 requires minimum 25%; v2.1 exceeds for anti-gaming margin).

## 4. Dataset Taxonomy

- **Level 1:** Research, Industry, Reliability, Safety, Quality.
- **Level 2:** Language, Domain, Difficulty, Track, Task.
- **Level 3:** Individual benchmark sample.

## 5. Sample Metadata Schema (per #13)

```json
{
  "id": "",
  "benchmark_version": "2.1",
  "track": "",
  "domain": "",
  "language": "",
  "difficulty": "",
  "task_type": "",
  "source": "",
  "created_at": "",
  "reviewer_1": "",
  "reviewer_2": "",
  "iaa_kappa": 0.0,
  "reviewer_3": null,
  "visibility": "public|hidden",
  "question": "",
  "gold_answer": "",
  "rubric_id": ""
}
```

## 6. Difficulty Framework

Difficulty is not subjective.

- **Easy** — single-step. Example: `What is GST?`
- **Medium** — requires interpretation. Example: `Do I need GST registration?`
- **Hard** — requires reasoning. Example: `My turnover is ₹38L but I operate in multiple states. Do I need GST?`
- **Expert** — requires multiple regulations. Example: `I operate as an LLP across states and sell digital products internationally.`

| Difficulty | Target |
|---|---|
| Easy | 25% |
| Medium | 45% |
| Hard | 25% |
| Expert | 5% |

## 7. Language Distribution

No language exceeds 20%. Target:

| Language | Share |
|---|---|
| Hindi | 15% |
| Marathi | 10% |
| Tamil | 10% |
| Telugu | 10% |
| Bengali | 10% |
| Gujarati | 10% |
| Kannada | 10% |
| Malayalam | 10% |
| Punjabi | 7.5% |
| Odia | 7.5% |

## 8. Code-Mixed Dataset Standard

Categories: Hindi-English, Marathi-English, Tamil-English, Telugu-English, Gujarati-English, Bengali-English.

Example: `Bhai GST filing kal hai kya?`

Bad: 50 copies of same prompt. Good: differing grammar, slang, region, education levels.

## 9. Transliteration Dataset Standard

Every transliterated sample MUST have native-script + romanized versions.

## 10. Dialect Dataset Standard (line-itemed per #3)

Required dialects: **Bhojpuri, Awadhi, Magahi, Haryanvi, Chhattisgarhi**.

Target: **500 samples per dialect × 5 = 2,500 total** (1,500 public + 1,000 hidden, per §3 master table).

Tasks: QA, translation, intent detection.

## 11. Government Dataset

Required programs: PM-KISAN, Ayushman Bharat, DigiLocker, PMEGP, Startup India, Udyam, eShram, Skill India.
Target: 2,000 (per V3 §4 corrected table).

## 12. Finance Dataset
Topics: GST, PAN, TDS, UPI, Income Tax, MSME Loans, Banking. Target: 2,500.

## 13. Legal Dataset
Topics: DPDP, IT Act, Consumer Protection, RTI, Labour Law, Corporate Compliance. Target: 2,000.

## 14. Healthcare Dataset
Topics: Insurance, Ayushman Bharat, Vaccination, Public Health. Target: 1,500.

## 15. Education Dataset
Topics: UGC, AICTE, Scholarships, Admissions, Skill Development. Target: 1,500.

## 16. Customer Support Dataset
Sources: Telecom, Banking, SaaS, Government Services, E-Commerce. Target: 3,000 conversation samples.

(§§11–16 sum to 12,500, matching V3 §4 industry total — per fix #1.)

## 17. Reliability Dataset (split per #2)

| Sub-category | Target |
|---|---|
| Reliability — core (drift, consistency, formatting, long-context) | 2,500 |
| Hallucination | 1,500 |
| Adversarial | 1,500 |
| Dialect | 2,500 |
| **Total reliability** | **8,000** |

## 18. Hallucination Dataset
Categories: Government, Finance, Legal, Healthcare. Prompt intentionally contains false policy; expected: correction. Target: 1,500.

## 19. Safety Dataset
Categories: Fraud, Scams, Privacy, Dangerous Advice, Government Misinformation. Target: 2,500.

## 20. Adversarial Dataset
Categories: Prompt Injection, Jailbreaks, Context Poisoning, Tool Abuse, Retrieval Poisoning. Target: 1,500.

## 21. Multi-Turn Dataset

| Turns | Share |
|---|---|
| 1–2 | 40% |
| 3–5 | 40% |
| 6–10 | 20% |

## 22. Long Context Dataset

| Tier | Tokens | Share |
|---|---|---|
| Small | 4k | 40% |
| Medium | 16k | 30% |
| Large | 64k | 20% |
| Extreme | 128k | 10% |

## 23. Hidden Dataset Strategy

Public ~63% / Hidden ~37% across v2.1 (per §3).
Hidden dataset SHALL contain: hardest prompts, new prompts, adversarial prompts, unreleased workflows.

## 24. Dataset Collection Sources

Allowed: government websites, public documents, public policies, open data, human annotation.
Disallowed: copyright violations, private data, confidential records.

## 25. Human Annotation Guidelines (κ requirement per #13)

Annotators provide: gold answer, rubric, difficulty, domain, language.

**Two reviewers minimum per sample.** Inter-annotator agreement measured via **Cohen's κ** (categorical) or **Krippendorff α** (ordinal/continuous).

**Tiered acceptance thresholds.** Cohen's κ depends heavily on rubric clarity and reviewer pool depth. Tier-1 languages with deep reviewer pools and well-defined regulatory domains can sustain κ ≥ 0.7. Dialects and low-resource pairings cannot — holding them to the same bar would either block samples or force false agreement. Tier-2/3 thresholds are deliberately relaxed:

| Pairing | Accept threshold | Adjudicate threshold | Reject threshold |
|---|---|---|---|
| Tier-1 language × structured domain (Govt, Finance, Legal) | κ ≥ 0.70 | 0.40 ≤ κ < 0.70 | κ < 0.40 |
| Tier-1 language × open domain (CS, Education, Healthcare-info) | κ ≥ 0.65 | 0.35 ≤ κ < 0.65 | κ < 0.35 |
| Tier-2 language (Assamese, Urdu, Sanskrit, Konkani, Kashmiri) | κ ≥ 0.60 | 0.30 ≤ κ < 0.60 | κ < 0.30 |
| Tier-3 dialects (Bhojpuri, Awadhi, Magahi, Haryanvi, Chhattisgarhi) | κ ≥ 0.55 | 0.25 ≤ κ < 0.55 | κ < 0.25 |
| Subjective tasks (Quality, Code-mixed naturalness) | κ ≥ 0.55 | 0.25 ≤ κ < 0.55 | κ < 0.25 |

When 0.40 ≤ κ < accept threshold (or relevant tier band), a third reviewer adjudicates and rubric is reviewed for clarity. Below reject threshold, the sample is rejected and the rubric is revisited.

Per pairing, mean κ across the year SHALL meet the accept threshold for that tier. The Dataset Committee publishes annual κ reports broken out by tier.

## 26. Gold Answer Standard

Every gold answer:
```json
{
  "correct": "",
  "acceptable": [],
  "incorrect": []
}
```
Includes: correct response, alternative responses, common errors, failure modes.

## 27. Benchmark Leakage Prevention

Detect: GitHub copies, dataset memorization, public benchmark overlap, synthetic duplication.
Maximum duplicate threshold: **1%**.

## 28. Dataset Quality Gates

Every sample passes: language validation, domain validation, formatting validation, metadata validation, gold-answer validation, **κ validation per #13**.

## 29. Dataset Auditing

Every release: 10% manual audit by Dataset Committee + Audit Committee spot-checks.

## 30. Sample Retirement Policy

Retire if: obsolete, incorrect, ambiguous, legally invalid. Retired samples archived (kept for replay of prior version scores).

## 31. Benchmark Evolution Policy (clarified per #12)

Each release introduces 10–20% new samples. **Each release bumps the minor version** (v2.1 → v2.2 → v2.3). Old versions stay frozen forever. Cross-version score comparison is not normative.

## 32. Dataset Acceptance Criteria

Dataset accepted only if:
- Coverage targets met.
- Difficulty distribution within ±2% of target.
- Language balance maintained.
- Hidden set secured.
- Duplicate rate ≤ 1%.
- Mean κ ≥ 0.7 per language-domain pair.

## 33. Dataset Health Metrics

Track: language coverage, domain coverage, difficulty distribution, duplicate rate, **Failure Discovery Rate** (per #8).

## 34. Failure Discovery Rate (reframed per #8)

**This is a dataset-quality metric, not a model-scoring metric.** A benchmark whose dataset never surfaces model failures is uninformative.

Formula: `Unique failures discovered / Total samples`.

FDR is reported alongside dataset health metrics. It does **not** enter the model-scoring formula. v2.0 framing of FDR as "the most important metric" is withdrawn — it confused dataset quality with model ranking.

## 35. Pilot Directive (new — fixes #18, #19)

Before scaling to 31,000 samples, the Dataset Committee SHALL:
1. Build a **500-sample Hindi-GST pilot** end-to-end (covering Research + Industry-Finance + Reliability + Safety + Quality).
2. Run the pilot through V5 §42 pilot harness against ≥ 3 models (e.g. Sarvam-2, GPT-4, Llama-3-Indic).
3. Log every spec ambiguity, normalization edge case, and rubric disagreement encountered.
4. Feed findings into v2.2 spec revisions and V8 (Operations Manual) authoring.

Until pilot completes, v2.1 is a **draft normative spec**, not an active benchmark.

## 36. Dataset Success Criteria

The Dataset Bible succeeds if:
1. Models cannot easily memorize it.
2. It exposes real Indian AI weaknesses.
3. It remains relevant within version (years per V1 P3).
4. It differentiates strong and weak systems.
5. It reflects actual Indian users.
6. Mean κ ≥ 0.7 sustained across releases.
