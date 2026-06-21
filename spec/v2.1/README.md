# IndicEval Standard (IES) v2.1 — Spec Index

**Status:** Draft normative spec (not yet active benchmark — pilot pending).
**Supersedes:** v2.0 (frozen forever per V1 P3).

## Read in this order

1. **[CHANGELOG-v2.0-to-v2.1.md](CHANGELOG-v2.0-to-v2.1.md)** — what changed and why (23 fixes mapped).
2. **[Volume 1 — Constitution.md](Volume-1-Constitution.md)** — governance, versioning, scoped reproducibility, Western-judge limitation.
3. **[Volume 6 — Dataset Bible.md](Volume-6-Dataset-Bible.md)** — reconciled sample budgets (~31k), κ requirement, pilot directive.
4. **[Volume 7 — Scoring Bible.md](Volume-7-Scoring-Bible.md)** — penalty math, normalization, statistical tests, certification gate.
5. **[Volume 4 — Reliability/Safety/Quality.md](Volume-4-Reliability-Safety-Quality.md)** — safety gate, judge framework (prod=GPT/Claude/Gemini, dev=Opus 4.7), revised consistency test.
6. **[Volume 3 — Industry.md](Volume-3-Industry.md)** — industry budget rebalanced to 12,500.
7. **[Volume 2 — Research.md](Volume-2-Research.md)** — pinned Indic-appropriate translation metrics.
8. **[Volume 5 — Architecture.md](Volume-5-Architecture.md)** — judge service split, audit certificates, pilot harness.

## Key changes from v2.0 (one-liners)

- Industry budget: 5k → 12.5k (sample math now sums correctly).
- Reliability budget: split into core/hallucination/adversarial/dialect = 8k.
- Total dataset: ~24k → ~31k.
- Safety penalty: -5 multiplier replaced with categorical Certification Gate.
- Penalty math: per-sample, baked into category scores, all scores floored at 0.
- Judge framework: prod (GPT+Claude+Gemini median, vendor recusal) vs dev (Opus 4.7 single).
- Consistency test: T=0 → T=0.7 with paraphrased prompts.
- Exact Match: defined Indic normalization pipeline (NFC, ZWJ strip, danda, etc.).
- Stats: paired bootstrap 10k iters, McNemar for binary, CI overlap for ranking.
- Translation: chrF++, COMET-22, BLEURT-20 pinned by checkpoint hash.
- Reproducibility claim scoped to public 75%; hidden 25% via Audit Committee certificates.
- IAA: Cohen's κ ≥ 0.7 per language-domain pair.
- FDR: reframed as dataset-quality metric (not model-scoring).
- Versioning: every refresh bumps minor version; old versions stay frozen.

## Residual issues (named, not fixed in v2.1)

- **R1.** Western-judge gap (deferred to v2.2 — Sarvam-2 + Krutrim added then).
- **R2.** Dataset doesn't exist yet (spec is upgraded; samples not written).
- **R3.** No pilot has run — unknown bugs only the Hindi-GST pilot will surface.
- **R4.** Cost model hand-wavy (V8 will size it after pilot).
- **R5.** Total budget grew ~24k → ~31k; funding implication unsized.

## Operational docs (alongside the spec)

- **[PILOT-Hindi-GST.md](PILOT-Hindi-GST.md)** — 500-sample pilot plan, scope, timeline, success criteria, stop conditions.
- **[COST-MODEL-pilot.md](COST-MODEL-pilot.md)** — order-of-magnitude budget for pilot (~$52k) and full v2.1 dataset (~$900k year-1, ~$300k year-2 recurring).

## Next steps

1. Run 500-sample Hindi-GST pilot (V5 §42 + V6 §35) using dev-mode judge (Opus 4.7).
2. Log spec ambiguities and rubric disagreements during pilot.
3. Write V8 (Operations Manual) from pilot findings — workflows, hardened cost model, charters.
4. Bump to v2.2 with V8 + spec refinements + Indic-judge addition (R1).
5. V9 (Cases Library) grows organically as samples land — not pre-written.

## Frozen v2.0 spec

The original v2.0 spec lives at the user's PDF (`IndicEval_Standard_v2.0.pdf`) and remains immutable per V1 P3. v2.1 is a forward release; cross-version score comparison is not normative.
