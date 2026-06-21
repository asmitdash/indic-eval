# IndicEval v2.1 — Working System

A complete, runnable benchmark for Indian-context AI systems. Plug a model in, get a scorecard out.

This is the operational implementation of the [v2.1 spec](spec/v2.1/README.md). The spec defines what to measure; this code measures it.

---

## Quick start (60 seconds, no API keys)

```bash
cd indic-eval
pip install -e ".[dev]"

# Sanity check — runs golden + broken mock; should produce IES≈100 and IES≈8 respectively.
indic-eval-v21 demo --out-dir reports

# Open reports/golden-mock.html and reports/broken-mock.html in a browser.
```

If the golden-mock IES is ≈100 and broken-mock triggers the Certification Gate, your install is healthy.

---

## Run against a real model

### AWS Bedrock (Claude Opus 4.7 — Asmit's default)

```bash
# .env should have AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
indic-eval-v21 evaluate \
  --model bedrock \
  --out-dir reports \
  --basename opus47-full
```

### Sarvam-2

```bash
indic-eval-v21 evaluate \
  --model sarvam \
  --model-id sarvam-2 \
  --api-key $SARVAM_API_KEY \
  --out-dir reports \
  --basename sarvam2-full
```

### Krutrim

```bash
indic-eval-v21 evaluate \
  --model krutrim \
  --model-id krutrim-spectre-v2 \
  --api-key $KRUTRIM_API_KEY
```

### OpenAI / GPT-4

```bash
indic-eval-v21 evaluate \
  --model openai \
  --model-id gpt-4-turbo \
  --api-key $OPENAI_API_KEY
```

### Anything else (vLLM, Ollama, custom)

```bash
indic-eval-v21 evaluate \
  --model openai-compat \
  --base-url http://localhost:11434/v1 \
  --model-id llama3.1
```

### With dev-mode judge for Quality scoring

The Quality layer is judge-scored. Without `--judge`, Quality falls back to F1 against the gold (heuristic). With `--judge`, Opus 4.7 on Bedrock acts as a single judge (advisory, not publishable as IES per V4 §12.1.2).

```bash
indic-eval-v21 evaluate --model sarvam --judge
```

Production benchmark mode (GPT + Claude + Gemini median with vendor recusal) is wired in `judge.py` as `ProdJudgePanel` but not yet exposed via CLI — pilot will surface this when GPT/Gemini API keys are available.

---

## What the report contains

For every model evaluated, you get three artifacts in `reports/`:

| File | Use |
|---|---|
| `<model>.json` | Full scorecard — every sample, every score, every penalty. Machine-parseable. |
| `<model>.md` | Markdown report — for GitHub PRs, Slack, email. |
| `<model>.html` | Self-contained HTML — for sponsors, stakeholders, no-internet demos. |

Each report shows:

- **Overall IES score** (0–100) with 95% confidence interval.
- **Certification level** — Platinum / Gold / Silver / Bronze / Not Certified.
- **Certification Gate status** — any Critical safety failure auto-flips to Not Certified, regardless of IES (V4 §11.3).
- **Layer breakdown** — Research (40%), Industry (25%), Reliability (15%), Safety (10%), Quality (10%).
- **Strengths** — layers and domains where the model is strong.
- **Weaknesses** — failure patterns: hallucinations, drift, refusal failures, weak domains.
- **Top 10 failures** — lowest-scoring samples with sample IDs for debugging.
- **Per-domain rollup** — finance vs government vs legal vs healthcare etc.
- **Methodology footer** — spec version, judge mode, known limitations.

---

## Architecture (file-by-file)

```
src/indic_eval/v21/
├── types.py            # Sample, Prediction, SampleEvaluation, Scorecard schemas (Pydantic)
├── normalization.py    # V7 §10 Indic normalization pipeline
├── metrics.py          # EM, F1, script/language detection, refusal heuristic, consistency
├── scoring.py          # Per-sample → Layer → Scorecard. Penalty math. Certification Gate.
├── adapters.py         # MockAdapter, BedrockClaudeAdapter, OpenAICompatAdapter (Sarvam/Krutrim/OpenAI/...)
├── judge.py            # OpusDevJudge (single), ProdJudgePanel (GPT+Claude+Gemini median, recusal)
├── dataset.py          # Loader for seed_v21.json + filters (by layer, language, max_per_layer)
├── pipeline.py         # run_evaluation(adapter, samples, judge=None) -> Scorecard
├── report.py           # render_markdown / render_html / write_reports
├── cli.py              # `indic-eval-v21` CLI
└── data/
    └── seed_v21.json   # 40 hand-crafted seed samples across all 5 layers
```

---

## Spec compliance map

Every v2.1 spec section that affects scoring is implemented and tested:

| Spec section | Implementation | Test |
|---|---|---|
| V7 §2 Master IES formula | `scoring.aggregate_scorecard` | `test_scorecard_weighted_sum_matches_v7` |
| V7 §6 Score floor at 0 | `scoring._evaluate_*` `max(0, ...)` | `test_floor_at_zero` |
| V7 §10 Indic normalization | `normalization.normalize_indic` | `test_normalization.py` (9 tests) |
| V7 §11 Exact Match | `metrics.exact_match` | `test_em_normalized_match` |
| V7 §12 Token F1 | `metrics.best_f1` | `test_f1_overlap` |
| V7 §16 Hallucination penalties | `scoring.SEVERITY_PENALTY` | `test_known_wrong_triggers_major_hallucination` |
| V7 §48 Certification bands | `scoring.certification_for` | `test_certification_bands` |
| V4 §11.3 Certification Gate | `scoring.aggregate_scorecard` + flag on `SampleEvaluation` | `test_scorecard_gate_overrides_certification` |
| V4 §6 Consistency (paraphrase set) | `metrics.consistency_score` (Jaccard fallback) | `test_consistency_high_when_same`, `test_consistency_low_when_different` |
| V4 §4–5 Drift detection | `metrics.script_drift`, `language_drift` | `test_drift_layer_detects_correct_script` |
| V4 §12.1 Judge framework | `judge.OpusDevJudge`, `ProdJudgePanel` | (integration; no API in unit tests) |

**Known divergence from spec (deferred to pilot):**

- V7 §13 translation metric variants (chrF++, COMET-22, BLEURT-20) — not implemented; current translation samples score via EM/F1 only. Pilot will load Indic-tuned checkpoints.
- V7 §14 paired bootstrap (10k iters) for CIs — current implementation uses normal-approximation CI; bootstrap is straightforward to add when the pilot needs it.
- V4 §6 BGE-M3 embedding cosine for consistency — current implementation uses token Jaccard. Correlates well on factual answers; embedding upgrade is one dependency away.
- V7 §15 retrieval scoring — RAG track not yet exposed in CLI.

These are explicit in the methodology footer of every report.

---

## What this gives you for sponsor conversations

Walking into Sarvam / Tech Mahindra / Jio / IndiaAI Mission, you can:

1. **Run their model on a real spec** in under 5 minutes — `indic-eval-v21 evaluate --model <them>`.
2. **Show the gap concretely** — "your IES is X; here are Y critical safety failures; here are Z hallucinations on regulated domains; cert is currently Bronze, not Gold."
3. **Show the upside** — "the gap to Gold is fixable with these specific improvements (refusal training on UPI scams, script-fidelity on dialect, regulatory grounding on DPDP)."
4. **Show the scaling story** — 40 samples → 31k via the [pilot plan](spec/v2.1/PILOT-Hindi-GST.md), funding sized in [cost model](spec/v2.1/COST-MODEL-pilot.md).

The benchmark exists. The pilot is the next $52k decision.

---

## Test suite

```bash
pytest tests/v21/ -v
```

45 tests, runs in <1s, no API keys required.

Tests cover:
- 9 normalization edge cases (NFC, ZWJ/ZWNJ, danda, mixed scripts).
- 14 metric tests (EM, F1, script detection, refusal heuristic in English + Hindi, consistency, hallucination signal).
- 13 scoring tests (per-sample dispatch, layer aggregation, certification bands, gate logic).
- 9 end-to-end tests (golden/broken mock runs, report generation, dataset filters).

---

## Adding your own dataset

The seed dataset is 40 samples. To run on your own:

```bash
# 1. Author samples in seed_v21.json schema. See src/indic_eval/v21/data/seed_v21.json.
# 2. Validate.
indic-eval-v21 validate path/to/your-samples.json
# 3. Evaluate.
indic-eval-v21 evaluate --model bedrock --dataset path/to/your-samples.json
```

---

## Why this is not the full v2.1

This is a **working spec implementation with a 40-sample seed**. The spec calls for ~31k human-reviewed samples (V6 §3). Closing that gap is the [pilot](spec/v2.1/PILOT-Hindi-GST.md) → full-dataset path that needs sponsor funding.

What this system delivers today:
- ✅ Runnable end-to-end against any model.
- ✅ Spec-aligned scoring math (penalty system, Certification Gate, layer weights).
- ✅ Indic normalization (NFC, ZWJ, danda) — tested against edge cases.
- ✅ Multi-vendor adapters (Bedrock, Sarvam, Krutrim, OpenAI-compat).
- ✅ Judge framework wired (dev-mode now, prod-mode panel ready).
- ✅ Reports that strengthen/weakness-analyze the model.
- ✅ 45 passing tests, deterministic, no API keys required for CI.

What needs the pilot before it's a normative IES score:
- 🟡 31,000-sample dataset (per V6 §3) — 40-sample seed is for demo/dev.
- 🟡 Production judge panel (GPT + Claude + Gemini median) — wired but not exposed in CLI.
- 🟡 Indic-tuned ML metrics (COMET-22, BLEURT, BGE-M3 embeddings).
- 🟡 Audit Committee certification of hidden-set scores (V1 §11).
- 🟡 Bootstrap CIs (currently normal-approx).

These are explicit in the report footer of every run, not hidden.
