# indic-eval

Eval harness, observability SDK, and public leaderboard for Indic LLMs.

The thesis: Indian LLM deployments are evaluated on English MMLU/HumanEval/HELM or
hand-rolled Hindi tests. Real failure modes — code-mixing (Hinglish), transliteration
drift, diglossia, dialect mismatch (Bhojpuri ≠ standard Hindi), script confusion —
are invisible until customers complain. Open datasets exist (AI4Bharat, IndicXTREME)
but are fragmented; no product wrapper, no observability, no leaderboard ops.

## Three layers, one repo

1. **Eval harness** (`indic_eval.harness`) — runs benchmarks against any
   `ModelAdapter` and produces a deterministic `Scorecard` JSON artefact.
2. **Observability SDK** (`indic_eval.observability`) — drop into your app, log
   every LLM call, run offline detectors (drift, script-switch, hallucination,
   empty-rate) over a window of logs.
3. **Leaderboard** (`indic_eval.leaderboard`) — FastAPI service: POST a Scorecard,
   GET the ranked list. Token-gated submissions.

## Five seed benchmarks (v1)

| Benchmark | Examples | What it tests |
|---|---|---|
| `indic-script-fidelity-v1` | 15 | User asks in Hindi → does the model answer in Devanagari, not Latin transliteration? Covers 10 Indic scripts. |
| `indic-transliteration-v1` | 12 | Hinglish input → does the model produce clean Devanagari (or accept Roman as fallback)? |
| `indic-code-mix-hinglish-v1` | 10 | Can the model hold a Hinglish register? Penalises pure-English and pure-Hindi alike. |
| `indic-diglossia-formal-v1` | 10 | Hindi has a wide register from heavily Sanskritised (govt) to Urdu-loanword colloquial (Bollywood). Tests register control. |
| `indic-dialect-bhojpuri-v1` | 10 | Bhojpuri / Awadhi / Magahi — 200M+ speakers, treated as "broken Hindi" by most LLMs. |

## Install

```bash
pip install -e ".[dev]"
cp .env.example .env
# fill in AWS creds for Bedrock; leave LEADERBOARD_TOKEN empty for open submissions
```

## Run

```bash
indic-eval list-benchmarks

# One benchmark against Claude Opus 4.7 on Bedrock (uses .env creds)
indic-eval run --model bedrock --benchmark indic-script-fidelity-v1 --max 5 --out scorecard.json

# Full slate
indic-eval run-all --model bedrock --out claude-scorecard.json

# Leaderboard service
indic-eval serve-leaderboard --port 8090 --store-file leaderboard.jsonl
# then submit:
curl -X POST http://localhost:8090/submit \
  -H "X-Token: $LEADERBOARD_TOKEN" \
  -H "Content-Type: application/json" \
  --data @claude-scorecard.json
```

## Observability SDK usage

```python
from indic_eval.observability import Tracer, FileLogStore, RunDetectors, \
    ScriptSwitchDetector, EmptyResponseDetector, DriftDetector

store = FileLogStore("./logs")
tracer = Tracer(deployment="customer-bot", model_id="global.anthropic.claude-opus-4-7",
                  store=store, provider="bedrock", language_hint="hi")

with tracer.span(prompt) as span:
    response = client.messages.create(...).content[0].text
    span.set_output(response)

# Offline, on a schedule:
runner = RunDetectors([ScriptSwitchDetector(), EmptyResponseDetector(), DriftDetector()])
alerts = runner.run(store.recent("customer-bot", n=500))
```

## Architecture

```
                  any LLM
                     │
           ┌─────────▼──────────┐
           │   ModelAdapter     │   echo | scripted | bedrock-claude
           │   (plug-in)        │
           └─────────┬──────────┘
                     │
       ┌─────────────┴───────────────┐
       │   Eval harness (run_all)    │
       └───┬────────────┬────────────┘
           ▼            ▼
        Scorecard    Benchmark JSONs (5 in v1)
        (artefact)   under benchmarks/data/

       ┌─────────────────────────────┐
       │   Leaderboard API           │   POST /submit   GET /leaderboard
       │   (FastAPI, file or memory) │
       └─────────────────────────────┘

       ┌─────────────────────────────┐
       │   Observability SDK         │   Tracer.span() in your app
       │   + offline detectors       │   ScriptSwitch / Drift / Empty / Hallucination
       └─────────────────────────────┘
```

## Tested

49 unit + integration tests passing. Live Bedrock smoke: Claude Opus 4.7 scores
0.97+ on `script-fidelity-v1` for Hindi/Bengali, demonstrating the harness works
end-to-end on the real model.

## Roadmap

- v0.2: Tamil + Telugu dialect benchmarks; long-context Indic comprehension.
- v0.3: AI4Bharat IndicXTREME wrapper for cross-validation.
- v0.4: Postgres-backed observability store for prod scale.
- v0.5: Web dashboard for the leaderboard.

## Why this exists

Built by Cynergy as the technical moat under our AI-Governance compliance pack.
Indian model labs (Sarvam, Krutrim, JioBrain, Tech Mahindra Indus) and BFSI
deploying vernacular LLMs need an evaluation artefact that maps to the real
failure modes — not English MMLU. NVIDIA NeMo Evaluator's Indic extension is the
obvious distribution play.

Per Asmit's CLAUDE.md model policy: defaults to `global.anthropic.claude-opus-4-7`
on Bedrock for the judge model. Override with `INDIC_EVAL_JUDGE_MODEL` env var.

## License

MIT (when published). Currently private to Cynergy.
