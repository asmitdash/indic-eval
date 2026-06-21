"""Evaluation pipeline — submission → predictions → scoring → scorecard.

Single entry point: run_evaluation(adapter, samples, judge=None) -> Scorecard.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .adapters import GenerationConfig, ModelAdapter, MockAdapter
from .judge import Judge
from .scoring import (
    aggregate_layer, aggregate_scorecard, evaluate_sample, LAYER_WEIGHTS,
)
from .types import Layer, Sample, SampleEvaluation, Scorecard


@dataclass
class RunOptions:
    temperature: float = 0.0
    max_tokens: int = 512
    top_p: float = 1.0
    cost_per_call_usd: float = 0.0    # for cost estimation; user-supplied
    progress: bool = True


def _generate_safe(adapter: ModelAdapter, prompt: str, sample_id: str,
                   cfg: GenerationConfig) -> tuple[str, float, Optional[str]]:
    """Returns (output, latency_ms, error_or_none)."""
    if isinstance(adapter, MockAdapter):
        adapter.set_current_sample(sample_id)
    t0 = time.perf_counter()
    try:
        out = adapter.generate(prompt, cfg)
        return out, (time.perf_counter() - t0) * 1000, None
    except Exception as exc:
        return "", (time.perf_counter() - t0) * 1000, f"{type(exc).__name__}: {exc}"


def run_evaluation(adapter: ModelAdapter,
                   samples: list[Sample],
                   judge: Optional[Judge] = None,
                   options: Optional[RunOptions] = None) -> Scorecard:
    """Run all samples through `adapter`, score per V7, return Scorecard.

    For Quality samples, calls `judge` if provided; otherwise falls back to F1.
    For Reliability samples with paraphrases, generates over each paraphrase
    and scores consistency.
    """
    options = options or RunOptions()
    cfg = GenerationConfig(
        temperature=options.temperature,
        max_tokens=options.max_tokens,
        top_p=options.top_p,
    )

    t_start = time.perf_counter()
    n_call_failures = 0
    total_calls = 0

    sample_evals: list[SampleEvaluation] = []
    for s in samples:
        # Primary call
        output, latency_ms, err = _generate_safe(adapter, s.question, s.id, cfg)
        total_calls += 1
        if err is not None:
            n_call_failures += 1

        # Paraphrase calls (consistency layer)
        paraphrase_outputs: list[str] = []
        if s.paraphrases:
            for pq in s.paraphrases:
                p_out, _, p_err = _generate_safe(adapter, pq, s.id, cfg)
                total_calls += 1
                if p_err is None:
                    paraphrase_outputs.append(p_out)

        # Judge (Quality only)
        judge_score = None
        if s.layer == Layer.QUALITY and judge is not None:
            try:
                judge_score = judge.score(s, output, model_under_test_vendor=adapter.vendor)
                total_calls += 1  # rough — judge is itself an LLM call
            except Exception:
                judge_score = None

        ev = evaluate_sample(s, output, paraphrase_outputs, judge_score)
        sample_evals.append(ev)

    duration = time.perf_counter() - t_start

    # Aggregate per layer
    layer_scores: dict[Layer, object] = {}
    for layer in Layer:
        evals_for_layer = [e for e in sample_evals if e.layer == layer]
        layer_scores[layer] = aggregate_layer(evals_for_layer, layer)

    cost_estimate = total_calls * options.cost_per_call_usd

    judge_mode = judge.mode if judge is not None else "no-judge"

    notes = (f"adapter={adapter.name} vendor={adapter.vendor} "
             f"calls={total_calls} call_failures={n_call_failures}")

    return aggregate_scorecard(
        layer_scores=layer_scores,
        sample_evaluations=sample_evals,
        model_name=adapter.name,
        model_vendor=adapter.vendor,
        judge_mode=judge_mode,
        duration_seconds=duration,
        cost_estimate_usd=cost_estimate,
        notes=notes,
    )
