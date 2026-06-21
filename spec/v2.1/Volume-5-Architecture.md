# IndicEval Standard (IES) v2.1 — Volume 5
## Technical Architecture, Infrastructure & Reference Implementation

**Status:** Draft v1.0
**Classification:** Normative
**Supersedes:** v2.0 Volume 5 (frozen)
**Changes from v2.0:** Judge service split into prod (3-judge median) vs dev (Opus 4.7 single) modes (#11, #22), audit-replay clarified for hidden-set certification (#7), pilot harness added (#18, #19).

---

## 1. Purpose

Volumes 1–4 + 6–7 define what must be measured and why. Volume 5 defines the engineering blueprint — how evaluations execute, scores are stored, leaderboards are generated, and integrity is maintained.

## 2. System Goals

- **Reproducible** on public set: same benchmark + same model + same version → same result (within drift limits).
- **Auditable**: every score traceable; hidden-set scores certified by Audit Committee.
- **Scalable**: small models, large models, agents, RAG, enterprise systems.
- **Extensible**: new tracks without redesign.
- **Pilot-friendly**: 500-sample runs must complete end-to-end on a single machine.

## 3. High-Level Architecture

```
                       IndicEval Platform
                              |
        ----------------------------------------------
        |              |              |              |
   Benchmark      Evaluation     Leaderboard     Reporting
   Engine         Pipeline       Service         Service
        |
   ---------------------------------------------------------
   |          |            |            |          |
 Research  Industry  Reliability    Safety     Quality
                                              (Judge Service:
                                               prod vs dev mode)
```

## 4. Core Services

| Service | Purpose |
|---|---|
| Benchmark Service | Dataset management, version pinning |
| Evaluation Service | Benchmark execution |
| Scoring Service | Score calculation per V7 |
| Judge Service | LLM-judge orchestration (prod: 3-judge; dev: Opus 4.7) |
| Leaderboard Service | Per-version rankings |
| Reporting Service | Reports |
| Audit Service | Verification, hidden-set certification |
| Submission Service | Model registration |
| Dataset Service | Dataset governance, κ tracking |

## 5. Repository Structure

```
indic-eval/
├── benchmark_core/
├── benchmark_tracks/
│   ├── research/
│   ├── industry/
│   ├── reliability/
│   ├── safety/
│   └── quality/
├── evaluators/
├── scorers/
│   ├── normalization/   # NFC, ZWJ stripping (V7 fix #15)
│   ├── metrics/         # EM, F1, BLEU, chrF++, COMET, BLEURT
│   └── stats/           # bootstrap, McNemar, CI
├── judges/
│   ├── prod/            # GPT, Claude, Gemini orchestrator
│   └── dev/             # Opus 4.7 single-judge
├── datasets/
│   └── v2.1/
│       ├── public/
│       └── hidden/      # encrypted, restricted access
├── submissions/
├── reports/
├── leaderboard/
├── api/
├── workers/
├── storage/
├── audit/
├── pilot/               # NEW: 500-sample Hindi-GST harness
├── tests/
├── docs/
└── cli/
```

## 6. Benchmark Engine

Loads datasets, selects tests, splits hidden/public, orchestrates evaluation. Resolves benchmark version, dataset, sample scheduling, and track routing.

## 7. Evaluation Pipeline

```
Submission → Validation → Benchmark Selection → Sample Execution
→ Scoring (per V7) → Aggregation → Report Generation → Leaderboard Update
```

## 8. Submission Service

Registers Model, Agent, RAG, or System candidates.
```json
{
  "name": "Sarvam-2",
  "version": "2.1",
  "track": "model",
  "endpoint": "...",
  "vendor": "Sarvam"
}
```
`vendor` field added for V4 §12.1 vendor recusal logic.

## 9. Evaluation Workers

Worker types: research-worker, industry-worker, reliability-worker, quality-worker, safety-worker. Each worker logs failures to the failure registry per V1 §17.

## 10. Queue Architecture

Recommended: Redis or RabbitMQ. Queues: `evaluation_queue`, `judge_queue`, `report_queue`, `audit_queue`.

## 11. Dataset Storage (Versioned)

```
datasets/
  v2.0/   # frozen
  v2.1/
    research/
    industry/
    reliability/
    safety/
    quality/
    dialects/
  v2.2/   # future
```

## 12. Dataset Schema

```json
{
  "id": "GST_001",
  "track": "industry",
  "language": "Hindi",
  "difficulty": "medium",
  "question": "...",
  "gold_answer": "...",
  "scoring": "exact_match_normalized",
  "rubric_id": "industry_finance_workflow_v2.1",
  "iaa_kappa": 0.82
}
```

## 13. Hidden Dataset Storage

Never committed, never downloadable, never in reports. Encrypted at rest (AES-256). Access restricted to Audit Committee members; access logged.

## 14. Scoring Service

Implements V7 formulas. Applies normalization pipeline (V7 fix #15), penalty math (V7 fix #5/#6), bootstrap CIs (V7 fix #14).

## 15. Scoring Engine Interface

```python
class Scorer:
    def normalize(self, text: str, language: str) -> str:
        """V7 fix #15: NFC → ZWJ/ZWNJ strip → lowercase → trim → punct strip"""

    def score(self, prediction, gold, rubric) -> Score:
        """Returns Score(value, ci_low, ci_high, penalties_applied)"""
```

## 16. Metric Library

Exact Match (normalized), F1, BLEU (SacreBLEU 2.4.x), chrF++ (word-order=2), ROUGE-L, BERTScore, COMET (`Unbabel/wmt22-comet-da`), BLEURT-20, Retrieval Precision, Retrieval Recall.

Checkpoint hashes for ML metrics live in `spec/v2.1/checkpoints.lock`.

## 17. Reliability Engine

Measures drift, consistency (paraphrased prompts at T=0.7 per V4 fix #9), hallucination, context retention.

## 18. Quality Engine (Judge Service)

### Production mode
Runs GPT, Claude, Gemini in parallel. Aggregation: median for 3-judge case; mean for 2-judge vendor-recusal case (V4 §12.1).

### Development mode
Single-judge Opus 4.7 via Bedrock. Output stamped `dev_only=true` so it cannot accidentally enter publishable leaderboards.

```python
class JudgeService:
    def evaluate(self, sample, model_vendor: str, mode: Literal["prod", "dev"]):
        if mode == "dev":
            return self._opus_judge(sample)  # advisory only
        # prod: filter judges by recusal
        active_judges = [j for j in self.judges if j.vendor != model_vendor]
        scores = parallel([j.score(sample) for j in active_judges])
        return median(scores) if len(scores) >= 3 else mean(scores)
```

## 19. Safety Engine

Measures fraud, privacy, jailbreaks, scams, misinformation. Emits both numeric Safety score and **certification status** (V4 §11.3 gate). A single Critical → status flips to Not Certified regardless of numeric score.

## 20. Failure Registry Service

```json
{
  "model": "",
  "track": "",
  "sample": "",
  "failure_type": "",
  "severity": ""
}
```
Used for analytics, audits, benchmark evolution.

## 21. Database

PostgreSQL.

## 22. Core Tables

`models`, `evaluations`, `submissions`, `scores`, `reports`, `failures`, `benchmark_versions`, `judge_runs` (new — for vendor-recusal audit trail), `iaa_kappa` (new — for κ tracking).

## 23. models
```
id, name, version, track, vendor, created_at
```

## 24. evaluations
```
id, submission_id, benchmark_version, status, started_at, completed_at, mode (prod|dev)
```

## 25. scores
```
evaluation_id,
research_score, industry_score, reliability_score, safety_score, quality_score,
overall_score,
certification_status,   # Platinum/Gold/Silver/Bronze/Not Certified (V7 §Certification + V4 §11.3)
ci_low, ci_high
```

## 26. failures
```
evaluation_id, sample_id, failure_type, severity, details, triggers_gate (bool)
```

## 27. judge_runs (new)
```
evaluation_id, sample_id, judge_vendor, score, dev_or_prod, recused (bool, with reason)
```

## 28. Audit Service

Replays evaluations, verifies samples, verifies aggregation. **For hidden-set scores:** Audit Service produces signed certificates; published score includes certificate hash. Third parties verify the certificate without seeing the dataset (V1 §11, fix #7).

## 29. Replay System

Every evaluation replayable. Store: prompt, output, metadata, score, judge_runs, normalization output.

## 30. Report Service

Executive, Technical, Failure, Reliability reports. All reports cite benchmark version explicitly (V1 P3).

## 31. Leaderboard Service

Per-version leaderboards: Overall, Research, Industry, Reliability, Safety, Quality, per-Language, per-Domain, per-Track. Cross-version comparison disabled by default in UI.

## 32. Leaderboard Schema
```json
{
  "rank": 1,
  "model": "Sarvam",
  "version": "2.1",
  "overall": 92.4,
  "ci": [91.2, 93.6],
  "certification": "Gold"
}
```

## 33. Benchmark API

Base path: `/api/v2.1`.

## 34. API Endpoints

`POST /submit` · `POST /evaluate` · `GET /leaderboard?version=2.1` · `GET /report` · `GET /benchmark` · `GET /version` · `POST /audit/verify` (new — verify hidden-set certificate).

## 35. CLI

```
indic submit
indic evaluate
indic evaluate --mode dev   # Opus 4.7 single-judge
indic report
indic leaderboard --version 2.1
indic pilot run --domain hindi-gst   # NEW: pilot harness
```

## 36. Authentication

v1: API keys. v2: OAuth.

## 37. Storage Architecture

PostgreSQL · Redis · S3-compatible (encrypted hidden datasets).

## 38. Caching

Redis. Cache benchmark metadata, leaderboards, reports. Never cache hidden-set contents.

## 39. CI/CD

Required: unit, integration, dataset, evaluation, normalization tests. Coverage 90%+. Pilot harness must pass on every PR touching scoring.

## 40. Testing Framework

Validates dataset, benchmark, scoring, leaderboard integrity. Includes:
- Normalization unit tests (Indic edge cases: ZWJ, conjuncts, nukta, transliteration variants).
- Bootstrap reproducibility test (same seed → same CI).
- Vendor-recusal correctness test.
- Certification-gate unit test (one Critical → Not Certified).

## 41. Self-Test Harness

Before release run `benchmark_self_test()`: determinism, drift, dataset leakage, judge stability, hidden-set security, κ thresholds.

## 42. Pilot Harness (new — fixes #18, #19)

```
indic pilot run --domain hindi-gst --samples 500 --models sarvam-2,gpt-4,llama-3-indic
```
Runs the v2.1 spec end-to-end on a 500-sample Hindi-GST set, producing:
- Full scorecard per model.
- Spec-bug log: any case where the spec text was ambiguous or contradicted itself in execution.
- Cost log: time + tokens per stage.

Pilot output drives V8 (Operations Manual). Until the pilot has run, v2.1 is a **draft normative spec**, not an active benchmark.

## 43. Open-Source Governance

Recommended license: Apache 2.0.

## 44. Reference Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js |
| Backend | FastAPI |
| Workers | Python |
| Database | PostgreSQL |
| Queue | Redis |
| Storage | MinIO / S3 |
| LLM judges (prod) | OpenAI, Anthropic, Google APIs |
| LLM judge (dev) | AWS Bedrock (Opus 4.7) |

## 45. Production Deployment

Docker · Kubernetes · AWS or Azure.

## 46. Reference Implementation Requirements

- Support all benchmark tracks.
- Support all scoring methods including normalization.
- Support hidden datasets with audit certification.
- Support audit replay.
- Support leaderboard generation.
- Support benchmark versioning.
- Support both prod and dev judge modes.
- Support pilot harness.

## 47. Acceptance Criteria

- All 7 volumes implemented.
- Reproducible scores on public set.
- Hidden datasets protected and certifiable.
- Audit replay succeeds.
- Stable leaderboards within version.
- Drift within limits.
- Self-test suite passes.
- Pilot harness produces valid scorecard.

## 48. Final Architecture Summary

Layer weights: 40% Research · 25% Industry · 15% Reliability · 10% Safety · 10% Quality.
Tracks: Model · Agent · RAG · System.
Engines: Benchmark · Evaluation · Scoring · Reliability · Safety · Quality (Judge) · Reporting · Leaderboard · Audit · Pilot.
