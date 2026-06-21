# IndicEval v2.1 — Pilot Plan: Hindi-GST 500

**Status:** Plan, not yet executed.
**Owner:** TBD (Standards Committee + Dataset Committee co-leads).
**Goal:** Pressure-test v2.1 spec end-to-end on a small, real-world slice before committing ~31k samples and six-figure annotation budget.

---

## 1. Why this pilot

Three things v2.1 cannot answer on paper:

1. **Does the spec actually scoreable in code?** Penalty math, normalization, certification gate, vendor recusal — all defined in V7 prose, none yet exercised on real model output.
2. **What's the κ reality on Hindi-GST?** v2.1 §V6 §25 sets κ ≥ 0.70 for Tier-1 × structured domains. We don't know if our rubrics produce that. If real-world κ is 0.55, the spec is broken at the threshold.
3. **What does it cost?** Fix #20 deferred the cost model to V8 because v2.0 estimates were guesswork. The pilot produces real per-sample numbers.

Picking Hindi-GST because:
- Hindi has the deepest reviewer pool (cheap to staff).
- GST has objective regulatory ground truth (clear gold answers).
- Code-mixed Hindi-English GST is the flagship use case (V2 §15).
- Failures here predict failures everywhere else.

## 2. Scope

| Dimension | Pilot scope |
|---|---|
| Samples | 500 |
| Languages | Hindi (native script + Romanized) |
| Domains | GST only (Finance subset of V3) |
| Tracks | Model only (skip Agent, RAG, System) |
| Layers covered | All 5 (Research, Industry, Reliability, Safety, Quality) — proportional |
| Models | Sarvam-2, GPT-4, Llama-3-Indic (Indic-tuned variant) |
| Judge mode | **Dev mode (Opus 4.7 single-judge, Bedrock).** Cost-efficient; pilot scores are not publishable as IES per V4 §12.1.2. |
| Reviewers | 2 native Hindi speakers with GST domain familiarity + 1 adjudicator |

## 3. Sample allocation across the 500

Mirrors v2.1 master weights so the pilot is structurally proportional, not just a Research stress-test:

| Layer | Pilot samples | v2.1 weight | Notes |
|---|---|---|---|
| Research (Hindi-GST QA + IE + Translation) | 200 | 40% | EM, F1, COMET-22 hot path |
| Industry (GST workflows) | 125 | 25% | Eligibility, regulatory accuracy |
| Reliability (drift, consistency, hallucination) | 75 | 15% | Includes 5 paraphrases × 15 prompts for consistency |
| Safety (GST-fraud refusal) | 50 | 10% | Tests Certification Gate |
| Quality (judge calibration on GST QA) | 50 | 10% | Opus 4.7 judge |

Within each layer, difficulty follows V6 §6: 25% easy / 45% medium / 25% hard / 5% expert.

## 4. What the pilot must produce

### 4.1 Mandatory outputs

1. **Scorecards** — full v2.1 scorecard per model: per-layer scores + overall IES + certification status + 95% bootstrap CIs. Format per V5 §32.
2. **Spec-bug log** — every place during execution where the spec was ambiguous, contradictory, or under-specified. One row per ambiguity, with the V-section reference and the workaround applied.
3. **Cost log** — wall-clock time + token spend per stage (annotation, evaluation, judging, scoring). Broken out by model.
4. **κ report** — actual κ per Hindi-GST sub-domain (eligibility, process, regulatory). Used to validate / break V6 §25 thresholds.
5. **Normalization stress test** — pre/post normalization Exact Match deltas. Quantifies how much V7 §10 actually buys us on Indic.
6. **Certification Gate hit-rate** — how many Critical safety failures triggered the gate, across the 3 models. Validates that gate fires the way we think.

### 4.2 Stop-the-pilot conditions

- Any v2.1 formula produces NaN, negative, or >100 score → halt, fix spec, restart.
- κ < 0.40 across Hindi-GST → rubric is broken; rewrite before continuing.
- Bootstrap CIs collapse to zero width or exceed ±20 → statistical method needs rework.

## 5. Pilot harness (V5 §42)

Single command:
```
indic pilot run --domain hindi-gst --samples 500 --models sarvam-2,gpt-4,llama-3-indic --judge-mode dev
```

Harness responsibilities:
- Load 500 samples from `datasets/v2.1/pilot/hindi-gst/`.
- Route per layer to correct evaluator.
- Apply V7 §10 normalization before EM.
- Compute V7 §16, §18, §20 penalties at sample level.
- Aggregate via V3/V4 formulas; floor at 0.
- Produce signed audit certificate for hidden subset (V1 §11).
- Emit the 6 mandatory outputs above as JSON + Markdown.

Hardware target: pilot completes on a single workstation (≤ 64 GB RAM, 1 GPU optional for COMET/BLEURT) within 24 hours wall-clock.

## 6. Timeline (assumes solo-to-2-person execution)

| Phase | Duration | What ships |
|---|---|---|
| Phase 0 — rubric drafting | 1 week | Hindi-GST rubric pack, gold-answer schema, reviewer training doc |
| Phase 1 — sample creation | 2 weeks | 500 samples, 2-reviewer pass, κ measured, adjudication for low-κ |
| Phase 2 — harness build | 1 week | V5 §42 pilot harness wired to v2.1 scorers |
| Phase 3 — execution | 3 days | 3 models scored; Opus 4.7 judges Quality |
| Phase 4 — analysis | 1 week | 6 mandatory outputs written; spec-bug log triaged |
| Phase 5 — v2.2 spec revisions | 1 week | Apply pilot findings; cut v2.2 RC |

**Critical path: ~6 weeks** with one dataset lead + one engineering lead.

## 7. Cost envelope

See `COST-MODEL-pilot.md` for line items. Rough top-line:

- **Annotation:** 500 samples × 2 reviewers × ~$3/sample (Hindi-GST is cheap; conjugate-language work is more expensive) ≈ **$3k**.
- **Adjudication:** ~10–15% of samples need third reviewer × $5/sample ≈ **$300**.
- **LLM API spend (model evaluation):** 500 samples × ~3 prompts/sample × 3 models × ~$0.01/call ≈ **$50** (model API).
- **Opus 4.7 judge spend (Bedrock):** 500 samples × ~$0.05/judge call ≈ **$25**.
- **Engineer time:** 6 weeks × 1.5 FTE × loaded rate — by far the dominant cost. Numbers below assume contract rates.

If staffed at $80/hour fully-loaded: 6 weeks × 60 hours/week × 1.5 people × $80 ≈ **$43k engineer cost**.

**Pilot total: ~$47k** at this staffing assumption. The engineer time is the real number; everything else is rounding.

## 8. Decision points after pilot

The pilot is a fork:

- **Green light (most likely):** spec mostly survives, < 30 spec-bug entries, κ within tier thresholds. → Ship v2.2 with revisions, raise funding for full ~31k dataset.
- **Yellow light:** > 30 spec-bug entries OR κ < threshold for one tier. → Rewrite spec sections, second pilot (different domain/language), no fundraise yet.
- **Red light:** scoring formulas produce nonsensical results OR Certification Gate misfires. → IndicEval architecture needs rework before any production claim. Treat v2.0/v2.1 as research artifact; rebuild.

## 9. Out of scope for the pilot

- Agent track, RAG track, System track (require multi-component plumbing — defer).
- Tier-2 / Tier-3 languages (Hindi-only validates the pipeline).
- Multi-domain (GST-only is enough to break the spec).
- Production judge panel (GPT/Claude/Gemini median is the right thing for IES scores; pilot uses dev mode for cost).
- Public leaderboard publication (pilot scores are advisory only per V4 §12.1.2).

## 10. Success definition

Pilot succeeds if and only if:

1. All 6 mandatory outputs ship.
2. Spec-bug log has < 30 entries that require V-section rewrites.
3. κ ≥ tier threshold (V6 §25) on at least 2 of the 3 GST sub-domains.
4. Cost-per-sample number is published (not just "high" or "low").
5. Standards Committee + Audit Committee sign off on extending to full v2.2 dataset build.

If any one of these fails, the pilot's job is to tell us so before we burn the full budget.
