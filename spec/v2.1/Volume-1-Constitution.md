# IndicEval Standard (IES) v2.1 — Volume 1
## Constitution, Governance & Benchmark Philosophy

**Status:** Draft v1.0
**Classification:** Normative
**Supersedes:** v2.0 Volume 1 (frozen)
**Changes from v2.0:** Versioning rule codified (#12), reproducibility claim scoped (#7), governance staffing targets added (#21), Western-judge limitation acknowledged (#22).

---

## 1. Executive Summary

IndicEval Standard (IES) is a benchmarking framework for evaluating Indian LLMs, AI agents, RAG systems, and complete AI applications across multilingual, code-mixed, transliterated, domain-specific, safety-critical, and production-reliability scenarios.

IndicEval determines:
- Which systems perform best in Indian contexts.
- Which systems remain reliable under production conditions.
- Which systems can safely handle government, legal, financial, and multilingual workflows.
- Which systems demonstrate stable behavior across languages, dialects, and interaction styles.

IndicEval functions as Research, Industry, Reliability, Safety, and Quality benchmark within a single ecosystem.

## 2. Mission

Become the standard framework for evaluating AI systems in Indian linguistic, cultural, governmental, financial, legal, and enterprise environments. Priorities: reproducibility (within stated scope), transparency, stability, practical utility, scientific rigor.

## 3. Problem Statement

Unchanged from v2.0: language-centric evaluation gap, lack of code-mixed evaluation, lack of enterprise evaluation, lack of production reliability measurement.

## 4. Scope

IndicEval evaluates Models, Agents, RAG systems, and complete Applications.

## 5. Non-Goals

- Not a chatbot arena.
- Not a marketing platform.
- Not a safety certification (high scores ≠ regulatory compliance).
- Not legal certification.

## 6. Stakeholders

Model providers (Sarvam, Krutrim, JioBrain), research institutions (AI4Bharat, IITs, IIITs), enterprises (Tech Mahindra, Infosys, TCS), startups, government agencies.

## 7. Benchmark Philosophy — Five Principles

### P1 — Reproducibility (scoped)
Identical evaluations on the **public dataset (75% of scoring weight)** produce nearly identical results — max drift ±1%. The hidden 25% is reproducible only by the Audit Committee, which publishes signed score certificates. *(Fix #7: prior v2.0 wording implied full reproducibility, which is impossible with hidden datasets.)*

### P2 — Transparency
All methodologies, scoring equations, and benchmark versions are public. Hidden dataset *contents* are private; hidden dataset *governance* is public.

### P3 — Version immutability + forward releases
Released benchmark versions never change. v2.0 stays v2.0 forever. Updates ship as new minor versions: v2.1, v2.2, v2.3. Each version maintains a separate leaderboard. Cross-version comparisons are not normative. *(Fix #12: prior v2.0 had immutability principle but also "10–20% new samples per release" with no explicit version-bump rule.)*

### P4 — Production relevance
Every benchmark task represents a realistic use case.

### P5 — Anti-gaming
Design actively resists memorization, prompt leakage, hardcoded responses, and leaderboard optimization.

## 8. Benchmark Architecture — Five Layers

| Layer | Weight | Measures |
|---|---|---|
| L1 Research | 40% | Language understanding, translation, summarization, reasoning |
| L2 Industry | 25% | Government, finance, legal, healthcare, education, customer support |
| L3 Reliability | 15% | Consistency, drift, hallucinations, formatting stability |
| L4 Quality | 10% | Helpfulness, clarity, completeness via consensus LLM judges |
| L5 Safety | 10% | Fraud, scams, dangerous advice, privacy violations — **with certification gate (V4 §Safety)** |

## 9. Evaluation Tracks

| Track | Evaluates / Input → Output |
|---|---|
| A — Model | Base model capability. Model endpoint → Model score. |
| B — Agent | Tool-using systems. Agent endpoint → Agent score. |
| C — RAG | Retrieval systems. Retriever + KB → RAG score. |
| D — System | Complete applications. Application endpoint → System score. |

## 10. Public / Hidden Dataset Policy

Hybrid: 75% public (reproducibility) + 25% hidden (anti-gaming). Hidden datasets are not disclosed. Reproducibility claim applies to the public 75% only (P1 scoping).

## 11. Governance Structure

Three standing committees. Each requires founding membership before v2.1 launch.

| Committee | Purpose | Founding members (target) |
|---|---|---|
| Standards Committee | Releases, policies, benchmark evolution | 3 (1 academic, 1 industry, 1 government) |
| Dataset Committee | Dataset quality, reviewer oversight, κ audits | 3 + 2 per Tier-1 language |
| Audit Committee | Score verification, hidden-set certification, integrity | 3 (independent of model providers) |

Charter drafting and member identification deferred to V8 (Operations Manual). Until staffed, IndicEval scores are advisory, not normative. *(Fix #21.)*

## 12. Release Process

```
Proposal → Review → Audit → Public Comment (minimum 30 days) → Release Candidate → Final Release
```

Each Final Release bumps the minor version (P3). v2.0 is immutable. v2.1 is the first forward release.

## 13. Leaderboard Philosophy

Maintained leaderboards per benchmark version: Overall, Research, Industry, Reliability, Safety, Quality, per-Language, per-Domain, per-Track. Single-score rankings shall not be the sole representation.

## 14. Score Stability Requirements

| Scenario | Maximum Drift |
|---|---|
| Same Day | 0.5% |
| Same Week | 1% |
| Same Month | 1.5% |

Higher drift triggers Audit Committee investigation.

## 15. LLM Judge Governance

LLM judges contribute at most 10% of total benchmark score (Quality layer).

### 15.1 Production benchmark
Approved judges: GPT, Claude, Gemini. Final judge score = median(GPT, Claude, Gemini), with vendor recusal: when judging model X from vendor V, the judge from vendor V is excluded; remaining two judges aggregate by mean. *(Fix #11.)*

### 15.2 Development / pilot
Single-judge mode permitted using Opus 4.7 (Bedrock) for cost and iteration speed. Development scores are not publishable as IES scores.

### 15.3 Acknowledged limitation (residual issue R1)
All three production judges are Western-trained frontier-lab models. For an Indian-context benchmark, this is the same gap IndicEval exists to address, one level up. **This is a known limitation of v2.1.** v2.2 plans to add Sarvam-2 and Krutrim, moving to median-of-5. *(Fix #22 acknowledged but deferred per project decision.)*

## 16. Benchmark Self-Test Framework

| Test | Expectation |
|---|---|
| Determinism | <0.5% variance on public set |
| Judge drift | <5% ranking movement (raised from <2% per fix #10, pending empirical validation) |
| Prompt leakage | Detection enabled |
| Overfitting | Hidden-set performance maintained |
| Language stability | No unexpected language switching |
| Code-mixed stability | Stable rankings |
| Failure-registry validation | 100% failure logging |

## 17. Failure Registry

Every failure recorded and auditable. Sample entry:
```json
{
  "model": "sarvam-2",
  "benchmark": "2.1",
  "track": "finance",
  "case": "GST_0123",
  "failure_type": "hallucination",
  "severity": "critical"
}
```

## 18. Success Criteria

- Reproducible results on public set.
- Hidden-set integrity preserved (Audit Committee attestation).
- Voluntary industry submissions.
- Transparent methodology.
- Stable rankings within version; cross-version is not normative.
- Exposes meaningful weaknesses other benchmarks miss.
