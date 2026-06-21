# IndicEval Standard (IES) v2.1 — Volume 3
## Industry Benchmark Specification

**Status:** Draft v1.0
**Classification:** Normative
**Supersedes:** v2.0 Volume 3 (frozen)
**Changes from v2.0:** Sample budget reconciliation (#1) — Industry total raised from 5,000 to 12,500 to match domain targets. Domain-level sub-budgets explicitly listed.

---

## 1. Purpose

Evaluates whether an AI system can operate in real Indian business, public service, enterprise, legal, healthcare, education, and customer-support environments. Measures workflow completion, domain reasoning, decision support, multi-step interactions, enterprise readiness, and user-outcome quality. Contributes 25% of total IndicEval score.

## 2. Core Philosophy

Research asks: *Can the model answer?*
Industry asks: *Can the model complete the task correctly?*

**Bad test:** `What is GST?`

**Good test:**
```
I run a small business in Pune. My annual turnover is ₹32 lakh.
Do I need GST registration? What are the next steps?
```

## 3. Industry Domains & Weights

| Domain | Weight |
|---|---|
| Government | 20% |
| Finance | 20% |
| Legal & Compliance | 20% |
| Healthcare | 15% |
| Education | 15% |
| Customer Support | 10% |

## 4. Dataset Structure (corrected per fix #1)

| Domain | Public | Hidden | Total |
|---|---|---|---|
| Government | 1,200 | 800 | 2,000 |
| Finance | 1,500 | 1,000 | 2,500 |
| Legal | 1,200 | 800 | 2,000 |
| Healthcare | 900 | 600 | 1,500 |
| Education | 900 | 600 | 1,500 |
| Customer Support | 1,800 | 1,200 | 3,000 |
| **Total Industry** | **7,500** | **5,000** | **12,500** |

*Rationale for budget increase:* v2.0 §3 stated "5,000 workflows" but every domain section listed targets summing to 12,500. v2.1 honors the domain targets and updates the total. Domain weights (above) determine scoring contribution; sample counts determine statistical power.

## 5. Government Framework (20%)

Assist users with government schemes, applications, eligibility, documentation, and digital public infrastructure: PM-KISAN, Ayushman Bharat, DigiLocker, Startup India, PMEGP, Skill India, eShram, Udyam.

**Example:** `User: I am a farmer from Maharashtra. Can I apply for PM-KISAN?`
**Expected:** eligibility explanation, missing-information request, no hallucinated benefits.

### Government Scoring
| Metric | Weight |
|---|---|
| Eligibility Accuracy | 30% |
| Process Accuracy | 30% |
| Document Accuracy | 20% |
| Follow-up Questions | 10% |
| Hallucination Avoidance | 10% |

## 6. Finance Framework (20%)

Domains: GST, PAN, TDS, UPI, Income Tax, MSME finance, digital payments.

**Example:** `User: My UPI payment was deducted but receiver did not receive money.`
**Expected:** correct explanation, correct resolution, no fabricated RBI rules.

### Finance Scoring
| Metric | Weight |
|---|---|
| Regulatory Accuracy | 40% |
| Workflow Accuracy | 30% |
| User Guidance | 20% |
| Hallucination Avoidance | 10% |

## 7. Legal & Compliance (20%)

Domains: DPDP, Consumer Protection, RTI, Labour Law, IT Act, Corporate Compliance, Data Governance.

**Example:** `User: Can a company store Aadhaar copies forever?`
**Expected:** legal explanation, caveats, no fabricated clauses.

### Compliance Scoring
| Metric | Weight |
|---|---|
| Legal Accuracy | 40% |
| Citation Accuracy | 20% |
| Risk Identification | 20% |
| Hallucination Avoidance | 20% |

## 8. Healthcare (15%)

Scope: healthcare support only — not diagnosis. Domains: Public Health, Vaccination, Ayushman Bharat, Health Insurance, Medical Information. **Forbidden:** medical diagnosis, prescription generation.

### Healthcare Scoring
| Metric | Weight |
|---|---|
| Information Accuracy | 40% |
| Safety | 30% |
| Clarity | 20% |
| Escalation Behavior | 10% |

## 9. Education (15%)

Domains: UGC, AICTE, Scholarships, Admissions, Skill Development, Exam Guidance.

**Example:** `Can I pursue M.Tech after MCA?`
**Expected:** accurate answer, requirement explanation, no fabricated eligibility.

## 10. Customer Support (10%)

Domains: Telecom, Banking, SaaS, E-Commerce, Government Services. Tasks: ticket handling, complaint resolution, escalation.

## 11. Workflow Completion Benchmark (most important section)

Research tests knowledge; Industry tests completion. Every workflow contains: Goal, Context, Constraints, Success Conditions.

**Example:**
```
Goal: Recover failed UPI payment
Success: correct root cause + correct resolution + no hallucinations
```

## 12. Agent Benchmark (Agent Track)

Measures tool usage, planning, multi-step reasoning, task completion, recovery. Weight inside Industry: 25%.

### Tool Use Evaluation
Example tools: Search, Calculator, Document Retriever, Knowledge Base.

| Metric | Weight |
|---|---|
| Correct Tool Selection | 40% |
| Correct Tool Usage | 30% |
| Correct Interpretation | 30% |

## 13. Multi-Turn Distribution

| Type | Weight |
|---|---|
| Single Turn | 40% |
| Multi Turn | 40% |
| Long Context | 20% |

## 14. RAG Evaluation Framework (RAG Track)

Measures retrieval quality.

### RAG Scoring
| Metric | Weight |
|---|---|
| Retrieval Accuracy | 35% |
| Grounding | 25% |
| Citation Accuracy | 20% |
| Hallucination Resistance | 20% |

## 15. System Evaluation (System Track)

Measures user experience, end-to-end completion, reliability, error handling, recovery.

## 16. Enterprise Benchmark

Special scenarios — HR Assistant, SOP Assistant, Internal Policy Bot, Compliance Bot, Knowledge Management — receive 20% bonus weighting within enterprise tests.

## 17. Hidden Workflow Policy

At least 40% of workflows hidden to prevent overfitting (consistent with v2.1 dataset table above: 5,000 hidden / 12,500 total = 40%).

## 18. Industry Failure Registry

Failure types: Wrong Process, Wrong Eligibility, Hallucinated Regulation, Missing Step, Wrong Tool, Wrong Retrieval.

## 19. Enterprise Readiness Score

```
ER = Government × 0.20
   + Finance × 0.20
   + Legal × 0.20
   + Healthcare × 0.15
   + Education × 0.15
   + Customer Support × 0.10
```

## 20. Industry Score Formula

```
Industry = Domain Score × 0.60
         + Workflow Completion × 0.20
         + Agent Evaluation × 0.10
         + RAG Evaluation × 0.10
```
Normalized to 0–100. Floored at 0 per V7 fix #6.

## 21. Industry Self-Test

| Test | Target |
|---|---|
| Workflow Stability | <1% score drift |
| Retrieval Drift | <2% score drift |
| Domain Balance | Balanced representation |
| Hidden Workflow Integrity | 100% protected |

## 22. Industry Success Criteria

- Workflows reflect real Indian use cases.
- Enterprise scenarios represented.
- Hidden sets secure.
- Stable scores within version.
- Failures expose practical weaknesses.
