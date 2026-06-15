"""The eval harness runner. Single-process, deterministic, reproducible."""
from __future__ import annotations
import statistics
import time
from typing import Optional

from ..models.types import (
    Benchmark, BenchmarkResult, ModelAdapter, ModelOutput, Scorecard, ScoredExample,
)
from .scorers import SCORERS, BenchmarkScorer, score_example


def run_benchmark(
    adapter: ModelAdapter,
    benchmark: Benchmark,
    scorer_name: str = "exact_match",
    max_examples: Optional[int] = None,
    custom_scorer: Optional[BenchmarkScorer] = None,
) -> BenchmarkResult:
    """Run an adapter over one benchmark and return a BenchmarkResult."""
    scorer = custom_scorer or SCORERS.get(scorer_name)
    if scorer is None:
        raise KeyError(f"Unknown scorer {scorer_name!r}")
    examples = benchmark.examples[:max_examples] if max_examples else benchmark.examples

    scored: list[ScoredExample] = []
    for ex in examples:
        t0 = time.monotonic()
        try:
            output = adapter.generate(ex.prompt)
        except Exception as exc:
            output = ""
            err = f"{type(exc).__name__}: {exc}"
            scored.append(ScoredExample(
                example_id=ex.id, metrics={scorer.primary_metric: 0.0},
                **{"pass": False}, output_excerpt=f"<error:{err}>",
            ))
            continue
        latency = int((time.monotonic() - t0) * 1000)
        out = ModelOutput(example_id=ex.id, output=output, latency_ms=latency)
        scored.append(scorer.fn(ex, out))

    metric_aggregates: dict[str, float] = {}
    if scored:
        all_keys: set[str] = set()
        for s in scored:
            all_keys.update(s.metrics.keys())
        for k in all_keys:
            vals = [s.metrics[k] for s in scored if k in s.metrics]
            if vals:
                metric_aggregates[k] = statistics.fmean(vals)

    primary_score = metric_aggregates.get(scorer.primary_metric, 0.0)
    n_passed = sum(1 for s in scored if s.pass_)
    return BenchmarkResult(
        benchmark_id=benchmark.id,
        benchmark_name=benchmark.name,
        primary_metric=scorer.primary_metric,
        primary_score=primary_score,
        metric_aggregates=metric_aggregates,
        n_examples=len(scored),
        n_passed=n_passed,
        examples=scored,
    )


def run_all(
    adapter: ModelAdapter,
    benchmarks: list[Benchmark],
    scorer_for: dict[str, str],
    max_examples: Optional[int] = None,
    weights: Optional[dict[str, float]] = None,
    notes: str = "",
) -> Scorecard:
    """Run a model over a slate of benchmarks and produce a Scorecard."""
    results: list[BenchmarkResult] = []
    for b in benchmarks:
        scorer_name = scorer_for.get(b.id, "exact_match")
        results.append(run_benchmark(adapter, b, scorer_name=scorer_name, max_examples=max_examples))

    weights = weights or {}
    total_weight = sum(weights.get(r.benchmark_id, 1.0) for r in results) or 1.0
    overall = sum(r.primary_score * weights.get(r.benchmark_id, 1.0) for r in results) / total_weight

    return Scorecard(
        model_id=adapter.model_id,
        model_provider=adapter.provider,
        benchmarks=results,
        overall_score=overall,
        notes=notes,
    )
