"""LLM-Judge for the Quality layer (V4 §12).

Two modes:
  - dev:   single-judge Opus 4.7 (Bedrock). Marked dev_only; cannot be
           published as IES per V4 §12.1.2.
  - prod:  median of GPT + Claude + Gemini, with vendor recusal (V4 §12.1.3).
           If model under test is from vendor V, judge V is excluded.

Heuristic fallback when no judge is available: token F1 against gold (handled
in scoring._evaluate_quality).
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Optional

from .adapters import (
    BedrockClaudeAdapter, GenerationConfig, ModelAdapter, OpenAICompatAdapter,
)
from .types import Sample


JUDGE_SYSTEM_PROMPT = """You are an evaluator for IndicEval v2.1, a benchmark for Indian-context AI systems.

You are given:
  - a question (possibly in Hindi, Marathi, code-mixed Hinglish, etc.)
  - a gold answer with optional acceptable variants
  - a candidate answer from the model under evaluation
  - a rubric

Score the candidate answer on a 0-100 scale across these dimensions, weighted per V7 §26:
  - Clarity (25%)
  - Completeness (25%)
  - Helpfulness (20%)
  - Reasoning (20%)
  - Structure (10%)

Return ONLY a JSON object:
{"clarity": 0-100, "completeness": 0-100, "helpfulness": 0-100, "reasoning": 0-100, "structure": 0-100, "overall": 0-100, "rationale": "one sentence"}

Be strict. A wrong answer cannot score above 30 regardless of style.
"""


def build_judge_prompt(sample: Sample, candidate: str) -> str:
    parts = [
        f"Question: {sample.question}",
        f"Gold answer: {sample.gold.correct}",
    ]
    if sample.gold.acceptable:
        parts.append(f"Acceptable alternatives: {', '.join(sample.gold.acceptable)}")
    if sample.gold.incorrect:
        parts.append(f"Common wrong answers: {', '.join(sample.gold.incorrect)}")
    parts.extend([
        f"Language: {sample.language}",
        f"Domain: {sample.domain}",
        f"Candidate answer: {candidate}",
        "",
        "Return JSON only.",
    ])
    return "\n".join(parts)


# ----------------------------------------------------------------------
# Judge interface
# ----------------------------------------------------------------------

class Judge(ABC):
    """Returns a score 0-100 for one (sample, candidate) pair, or None on failure."""
    mode: str = "dev"

    @abstractmethod
    def score(self, sample: Sample, candidate: str, model_under_test_vendor: str = "") -> Optional[float]:
        ...


# ----------------------------------------------------------------------
# Dev-mode: single-judge Opus 4.7
# ----------------------------------------------------------------------

class OpusDevJudge(Judge):
    """V4 §12.1.2 dev-mode single-judge using Opus 4.7 on Bedrock.

    Output is marked dev_only=True at the scorecard level by the pipeline.
    """
    mode = "dev"

    def __init__(self, model_id: str = "global.anthropic.claude-opus-4-7"):
        self.adapter = BedrockClaudeAdapter(model_id=model_id, name=f"judge:{model_id}")

    def score(self, sample: Sample, candidate: str, model_under_test_vendor: str = "") -> Optional[float]:
        prompt = JUDGE_SYSTEM_PROMPT + "\n\n" + build_judge_prompt(sample, candidate)
        try:
            raw = self.adapter.generate(prompt, GenerationConfig(temperature=0.0, max_tokens=512))
        except Exception:
            return None
        return _parse_judge_score(raw)


# ----------------------------------------------------------------------
# Prod-mode: GPT + Claude + Gemini median, vendor recusal
# ----------------------------------------------------------------------

class ProdJudgePanel(Judge):
    """V4 §12.1.1 + §12.1.3 prod judge panel.

    Accepts 1, 2, or 3 judges. Behavior:
      - 3 judges: median (V7 §25 prod default).
      - 2 judges: mean (also the recusal fallback when one is excluded).
      - 1 judge: that judge's score directly (degraded mode; report stamps it).

    Vendor recusal: when the model under test is from vendor V, judge V is excluded.
    """
    mode = "prod"

    def __init__(self,
                 gpt: Optional[ModelAdapter] = None,
                 claude: Optional[ModelAdapter] = None,
                 gemini: Optional[ModelAdapter] = None):
        self.judges = []
        if gpt is not None:
            self.judges.append(("openai", gpt))
        if claude is not None:
            self.judges.append(("anthropic", claude))
        if gemini is not None:
            self.judges.append(("google", gemini))
        if not self.judges:
            raise ValueError("ProdJudgePanel: at least one judge required")
        # Mode label changes if degraded: prod-3, prod-2, prod-1.
        self.mode = f"prod-{len(self.judges)}"

    def score(self, sample: Sample, candidate: str, model_under_test_vendor: str = "") -> Optional[float]:
        active = [(v, j) for (v, j) in self.judges if v != model_under_test_vendor]
        if not active:
            return None
        prompt = JUDGE_SYSTEM_PROMPT + "\n\n" + build_judge_prompt(sample, candidate)

        scores = []
        for vendor, j in active:
            try:
                raw = j.generate(prompt, GenerationConfig(temperature=0.0, max_tokens=512))
                s = _parse_judge_score(raw)
                if s is not None:
                    scores.append(s)
            except Exception:
                continue

        if not scores:
            return None
        if len(scores) >= 3:
            sorted_scores = sorted(scores)
            return sorted_scores[len(sorted_scores) // 2]   # median
        if len(scores) == 2:
            return sum(scores) / 2                          # mean
        return scores[0]                                     # single judge


def build_prod_judge(use_gpt: bool = True,
                      use_claude: bool = True,
                      use_gemini: bool = True,
                      gpt_model: str = "gpt-4-turbo",
                      claude_model: str = "global.anthropic.claude-opus-4-7",
                      gemini_model: str = "gemini-2.0-flash-exp") -> ProdJudgePanel:
    """Build a production judge panel selecting 1, 2, or 3 vendors.

    Auth env vars: OPENAI_API_KEY, AWS_* (Bedrock for Claude), GEMINI_API_KEY.
    """
    from .adapters import BedrockClaudeAdapter, GeminiAdapter, OpenAICompatAdapter

    kwargs = {}
    if use_gpt:
        kwargs["gpt"] = OpenAICompatAdapter(
            base_url="https://api.openai.com/v1",
            model=gpt_model,
            vendor="openai",
            name=f"judge:{gpt_model}",
        )
    if use_claude:
        kwargs["claude"] = BedrockClaudeAdapter(
            model_id=claude_model,
            name=f"judge:{claude_model}",
        )
    if use_gemini:
        kwargs["gemini"] = GeminiAdapter(
            model=gemini_model,
            name=f"judge:{gemini_model}",
        )
    return ProdJudgePanel(**kwargs)


# ----------------------------------------------------------------------
# Parse helpers
# ----------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_judge_score(raw: str) -> Optional[float]:
    """Pull 'overall' from a judge response. Tolerant of code fences and extra prose."""
    if not raw:
        return None
    candidates = _JSON_BLOCK_RE.findall(raw)
    for blob in candidates:
        try:
            obj = json.loads(blob)
        except Exception:
            continue
        if "overall" in obj:
            try:
                return max(0.0, min(100.0, float(obj["overall"])))
            except Exception:
                continue
        # If overall missing but components present, compute weighted sum.
        weights = {"clarity": 0.25, "completeness": 0.25,
                   "helpfulness": 0.20, "reasoning": 0.20, "structure": 0.10}
        if all(k in obj for k in weights):
            try:
                return sum(float(obj[k]) * w for k, w in weights.items())
            except Exception:
                continue
    return None
