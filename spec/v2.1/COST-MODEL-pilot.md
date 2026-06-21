# IndicEval v2.1 — Cost Model (Pilot + Full Dataset)

**Status:** Estimate, not yet validated by pilot.
**Purpose:** Size R5 (residual issue: total budget grew ~24k → ~31k, funding implication unsized).
**Dependency:** Numbers labeled `[ESTIMATE]` are guesses until the Hindi-GST pilot produces real per-sample data. Treat as order-of-magnitude only.

---

## 1. Why this exists now

V8 (Operations Manual) defers detailed cost modeling until after the pilot, because v2.0's estimates were guesswork. But Asmit is going to ask "what does this actually cost" before funding the pilot. This file is the order-of-magnitude answer that gets tightened post-pilot.

## 2. Two budgets, two questions

- **Pilot budget** answers: "Should I fund a 6-week test run?"
- **Full-dataset budget** answers: "Should IndicEval exist?"

## 3. Pilot budget (500 Hindi-GST samples)

### 3.1 Direct cost line items

| Line item | Quantity | Unit | Subtotal |
|---|---|---|---|
| Annotation (2 reviewers × 500 samples × Hindi-GST rate) | 1,000 reviews | $3 [ESTIMATE] | $3,000 |
| Adjudication (15% triggers third reviewer) | ~75 reviews | $5 [ESTIMATE] | $375 |
| Rubric authoring (paid domain expert, GST + Hindi) | 1 person × 1 week | $2,500 [ESTIMATE] | $2,500 |
| Model API spend (Sarvam-2, GPT-4, Llama-3-Indic) | ~4,500 calls | $0.01 avg | $50 |
| Judge spend (Opus 4.7 single, Bedrock) | ~600 calls | $0.05 avg | $30 |
| Embedding compute (BGE-M3 for consistency test) | one-time | local | $0 |
| Hosting / infra (single workstation, 6 weeks) | 6 weeks | $50/wk | $300 |
| **Direct subtotal** | | | **$6,255** |

### 3.2 Engineering time (dominant cost)

| Role | Weeks | Hours/wk | Loaded $/hr | Subtotal |
|---|---|---|---|---|
| Dataset lead (rubric, sample QA, κ tracking) | 4 | 50 | $80 | $16,000 |
| Engineering lead (harness, scoring, V5 §42 build) | 6 | 50 | $100 | $30,000 |
| **Engineering subtotal** | | | | **$46,000** |

### 3.3 Pilot total

**~$52k** at contractor rates.

If staffed by full-time employees on existing payroll: marginal cost = direct subtotal only ≈ **$6k**. The engineering time is real either way; whether it shows up as a budget line depends on staffing model.

### 3.4 What pilot money actually buys

- A scorecard for 3 models on 500 Hindi-GST samples (the artifact).
- 6 mandatory pilot outputs including spec-bug log and real κ numbers (the validation).
- Confidence to fundraise / commit the full-dataset budget — or kill the project before that mistake (the option value).

## 4. Full v2.1 dataset budget (~31,000 samples)

### 4.1 Annotation cost scales by language tier

Per-sample annotation cost varies by reviewer pool depth and rubric complexity:

| Tier | Languages | Per-sample rate (2 reviewers) [ESTIMATE] |
|---|---|---|
| Tier-1 high-resource | Hindi | $6 |
| Tier-1 mid-resource | Marathi, Bengali, Tamil, Telugu, Gujarati | $9 |
| Tier-1 lower-resource | Kannada, Malayalam, Punjabi, Odia | $12 |
| Tier-3 dialects | Bhojpuri, Awadhi, Magahi, Haryanvi, Chhattisgarhi | $18 |
| Code-mixed (Indic-English) | All Tier-1 pairs | +20% premium |
| Adversarial / Safety (specialist needed) | All | $25 |

### 4.2 Sample distribution × rates

Working from V6 §3 master table and V6 §7 language distribution:

| Bucket | Samples | Avg rate | Subtotal |
|---|---|---|---|
| Research (5 lang × ~1,400 each, mix of tiers) | 7,000 | $9 | $63,000 |
| Industry — high-resource lang share (~40%) | 5,000 | $7 | $35,000 |
| Industry — mid/low-resource lang share (~60%) | 7,500 | $11 | $82,500 |
| Reliability core | 2,500 | $9 | $22,500 |
| Hallucination (specialist factual review) | 1,500 | $15 | $22,500 |
| Adversarial | 1,500 | $25 | $37,500 |
| Dialects (Tier-3 rate) | 2,500 | $18 | $45,000 |
| Safety (specialist required) | 2,500 | $25 | $62,500 |
| Quality (judge calibration set) | 1,000 | $9 | $9,000 |
| **Annotation subtotal** | **31,000** | | **~$379,500** |

### 4.3 Adjudication

15% of samples trigger third reviewer × $7 avg = **~$33,000**.

### 4.4 Rubric authoring (one-time per domain × language)

~30 domain × language pairings × 1 week × $2.5k = **~$75,000**.

### 4.5 Engineering build

Full v2.1 platform per V5: ~9 services, REST API, leaderboard, audit replay, normalization library, judge service (prod + dev modes).

| Role | Months | Loaded $/mo | Subtotal |
|---|---|---|---|
| Engineering lead | 6 | $20k | $120,000 |
| Backend engineer | 4 | $15k | $60,000 |
| ML/eval engineer | 4 | $18k | $72,000 |
| Data engineer (datasets, hidden-set crypto) | 3 | $15k | $45,000 |
| **Engineering subtotal** | | | **$297,000** |

### 4.6 Production judge spend (recurring per evaluation)

For one full evaluation of one model across the v2.1 dataset:
- ~31,000 samples × ~3 prompts/sample = ~93,000 evaluation calls × ~$0.02 avg = **~$1,860 per model evaluation**.
- Production judges (GPT + Claude + Gemini median) on Quality samples: ~3,000 quality samples × 3 judges × ~$0.05 = **~$450 per model evaluation**.
- Per model per full IES run: **~$2,300**.

If the leaderboard runs 20 models initially: **~$46,000 first-year evaluation API spend**.

### 4.7 Infrastructure

| Item | Annual |
|---|---|
| Cloud (DB, queues, S3, APIs) | $24,000 |
| Hidden-set encrypted storage + access controls | $6,000 |
| **Infra subtotal** | **$30,000** |

### 4.8 Governance

Three committees, each 3+ founding members. If volunteer-based: $0 direct. If even one paid program manager: ~$80k/year.

Conservative: **$30,000** for part-time program management + meeting overhead.

### 4.9 Full v2.1 total — first-year estimate

| Bucket | Subtotal |
|---|---|
| Annotation | $379,500 |
| Adjudication | $33,000 |
| Rubric authoring | $75,000 |
| Engineering build | $297,000 |
| Production judge spend (year 1) | $46,000 |
| Infrastructure | $30,000 |
| Governance | $30,000 |
| **Year-1 total** | **~$890,000** |

Round to **~$900k** for conversational use. Year-2 recurring (no rebuild, ongoing eval + maintenance + 10–20% sample refresh) drops to **~$300k/year**.

## 5. What this number means

- This is **mid-six-figures, low-seven-figures** — squarely in foundation-grant territory (Wadhwani AI, Aspen, Nilekani Philanthropies, Mozilla Foundation), corporate sponsorship territory (Sarvam/Krutrim/Ola/JioBrain have direct interest), and government-program territory (MeitY's IndiaAI Mission has explicit benchmark funding).
- **Not VC-shaped.** IndicEval is benchmark infrastructure, not a startup. Trying to make it commercial creates the conflict-of-interest problem that kills benchmark credibility.
- **Single-org bootstrap is feasible** if Asmit's employer (Deloitte) or a major Indian model provider absorbs engineering cost in-kind.

## 6. Scenarios

| Scenario | Year-1 cost | Year-2 cost | Path |
|---|---|---|---|
| Pilot only, kill if findings poor | $52k | $0 | Defensible — answers "should this exist." |
| In-kind engineering, foundation-funded annotation | ~$500k | ~$200k | Most realistic for a credible benchmark. |
| Fully funded, fast build | ~$900k | ~$300k | Shortest path to v2.2 release; needs sponsor. |
| Open-source crowdsourced annotation | ~$300k (infra + governance) | ~$150k | Risk: κ collapses without paid reviewer rigor. |

## 7. Numbers most likely to be wrong

Calling out [ESTIMATE]-tagged guesses with the largest impact:

- **Indic annotation rates per sample.** Could be ±50%. Pilot resolves Hindi-GST; other tiers still guesses.
- **Engineering build months.** Could be 50% under for a polished platform. v2.0 §V5 architecture is 9 services + audit + leaderboard — that's a real 6+ months even with senior staff.
- **Adjudication rate.** Assumed 15%; could be 30% on dialects.
- **Specialist (Safety, Adversarial) rate.** Real rate depends on whether you can find domain experts at $25/sample or have to pay $60. Pilot won't tell us — only Safety pilot would.

## 8. Hard claims I'm willing to make

1. **Pilot is < $60k including engineering.** This is the actionable number. If Asmit can fund this, the rest of the project's existence becomes a real decision.
2. **Year-1 full v2.1 is in the $500k–$1M band.** Anyone who tells you it's $50k or $5M is wrong about scope.
3. **Year-2 recurring ≥ $200k.** Fixed cost of a credible benchmark — annotation refresh, judge API spend, governance.

The pilot exists to convert these from claims into measurements.
