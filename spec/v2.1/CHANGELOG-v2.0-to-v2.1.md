# IndicEval Standard — Changelog v2.0 → v2.1

**Status:** Normative
**v2.0 status:** Frozen forever (per immutability principle, fix #12).
**v2.1 status:** Active draft incorporating 23 corrections.

---

## Why v2.1 exists

v2.0 was a complete blueprint but contained 17 spec bugs and 6 structural gaps that surfaced under review. Per V1 P3 (version immutability), v2.0 cannot be modified. v2.1 is a forward release containing the fixes.

## Versioning rule (codified)

Every release that changes scoring formulas, dataset budgets, or rubric definitions bumps the minor version. v2.0 stays frozen. v2.1 supersedes it. Future changes (10–20% sample refresh per V6 §31) bump to v2.2, v2.3, etc. Leaderboards are always labeled by version. Cross-version score comparisons are not normative.

---

## The 23 fixes

### Spec bugs (17)

| # | Bug | Fix | Affected volume |
|---|---|---|---|
| 1 | Industry domain targets sum to 12,500 but budget is 5,000 | Industry budget raised to 12,500; domains scaled to fit | V3, V6 |
| 2 | Reliability budget 2,500 doesn't cover hallucination + adversarial + dialect | Split into named sub-budgets totaling 8,000 | V4, V6 |
| 3 | Dialect dataset (2,500) has no line item | Added as own row in master table | V6 |
| 4 | Safety penalty caps at -5 vs hallucination at -50 (inverted severity) | Critical safety failures = certification gate, not numeric penalty | V4, V7 |
| 5 | Penalty math undefined (per-sample/category/overall) | Specified: per-sample, averaged into category score, no double-deduction | V7 |
| 6 | Scores can go negative on bad runs | All category scores floored at 0 | V7 |
| 7 | "Independent reproduction" impossible with 25% hidden | Reproduction claim scoped to public 75%; Audit Committee certifies hidden 25% | V1, V7 |
| 8 | Failure Discovery Rate called "most important" but unweighted | Reframed as dataset-quality metric (not model-scoring); removed misleading framing | V6, V7 |
| 9 | Consistency at T=0 measures provider noise, not model | Run at T=0.7 with 5 paraphrased prompts | V4, V7 |
| 10 | Judge-replacement <2% claim asserted, not derived | Replaced with empirical leave-one-out on 1k samples; threshold raised to <5% | V7 |
| 11 | No recusal rule when GPT judges GPT | Vendor-recusal mandatory; remaining 2 judges use mean | V4, V7 |
| 12 | Immutability vs 10–20% new samples contradiction | Each refresh bumps minor version; old versions stay frozen | V1, V6 |
| 13 | 2 reviewers required but no agreement metric | Cohen's κ ≥ 0.7 required; below threshold → 3rd reviewer adjudicates | V6 |
| 14 | p<0.05 invoked but no test specified | Specified: paired bootstrap (10k iters) for continuous; McNemar for binary; CI overlap for ranking | V7 |
| 15 | Exact Match has no Indic normalization spec | NFC → strip ZWJ/ZWNJ → lowercase → trim → strip trailing punctuation | V7 |
| 16 | Score bands: 60–69 is both "Weak" and "Not Certified" | Dropped narrative bands; certification table is sole authority | V7 |
| 17 | Translation metrics not pinned to Indic-appropriate variants | chrF++ (word-order=2), COMET-22 (Unbabel/wmt22-comet-da), BLEURT-20; checkpoint hashes in V7 | V7 |

### Structural problems (6)

| # | Gap | Fix | Where |
|---|---|---|---|
| 18 | 24k-sample dataset doesn't exist | Pilot first: 500-sample Hindi-GST end-to-end before scaling | V6 §Pilot, V8 (deferred) |
| 19 | Spec untested against real model run | Pilot runs against 3 models (Sarvam, GPT-4, Llama-3-Indic); spec rewrites follow | V6 §Pilot |
| 20 | No cost model | Cost section deferred to V8 (post-pilot, so estimates are real) | V8 (deferred) |
| 21 | Committees named but unstaffed | Founding-member targets specified; charter drafting deferred to V8 | V1 §Governance, V8 |
| 22 | Three Western LLM judges — same gap benchmark exists to fix | **Acknowledged limitation; not fixed in v2.1.** Production benchmark uses GPT + Claude + Gemini median. Development uses Opus 4.7 single-judge. Indic-judge addition deferred to v2.2+. | V4 §Limitation |
| 23 | V8 (operations) and V9 (cases library) don't exist | V8 written *after* pilot; V9 grows organically with samples | Out of scope for v2.1 |

---

## Residual issues (not fixed in v2.1)

These remain known, named limitations:

- **R1.** Western-judge gap (fix #22 deferred). Three frontier-lab Western judges adjudicate Indian-context tasks. Mitigation in v2.2 will add Sarvam-2 and Krutrim to the panel; final score becomes median of 5.
- **R2.** Dataset still doesn't exist. Spec is upgraded but samples are not written.
- **R3.** No pilot has run. Unknown bugs only the Hindi-GST pilot will surface.
- **R4.** Cost model is hand-wavy. V8 will size it after the pilot.
- **R5.** Total dataset budget grew from ~24k to ~30k once sub-budgets are honored. Funding implication unsized.

---

## Reading order

1. This changelog
2. V1 (governance + versioning)
3. V6 (dataset budgets — biggest changes)
4. V7 (scoring math — biggest changes)
5. V4 (penalty fix, judge framework)
6. V3 (industry domain rebalance)
7. V2, V5 (minor edits)
