"""Per-benchmark scoring policies. Each benchmark plugs in a Scorer that decides
which metrics to compute on each example and how to roll them up.

A Scorer is a function (BenchmarkExample, ModelOutput) -> ScoredExample. The
runner applies it across the dataset and aggregates.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional

from ..models.types import BenchmarkExample, ModelOutput, ScoredExample
from ..models import scoring


@dataclass
class BenchmarkScorer:
    name: str
    fn: Callable[[BenchmarkExample, ModelOutput], ScoredExample]
    primary_metric: str
    pass_threshold: float = 1.0


# -- Concrete scorers --------------------------------------------------------

def _exact_match_scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    refs = ex.references or ([ex.reference] if ex.reference else [])
    if not refs:
        em = 0.0
    else:
        em = max(scoring.exact_match(out.output, r) for r in refs)
    return ScoredExample(
        example_id=ex.id, metrics={"exact_match": em},
        **{"pass": em >= 1.0}, output_excerpt=out.output[:200],
    )


def _contains_scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    refs = ex.references or ([ex.reference] if ex.reference else [])
    if not refs:
        c = 0.0
    else:
        c = max(scoring.contains(out.output, r) for r in refs)
    return ScoredExample(
        example_id=ex.id, metrics={"contains": c},
        **{"pass": c >= 1.0}, output_excerpt=out.output[:200],
    )


def _script_purity_scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    """Used by the script-fidelity benchmark: did the model answer in the expected script?"""
    expected = (ex.script.value if ex.script else "devanagari")
    purity = scoring.script_purity(out.output, expected)
    refs = ex.references or ([ex.reference] if ex.reference else [])
    cont = max((scoring.contains(out.output, r) for r in refs), default=0.0)
    metrics = {"script_purity": purity, "contains": cont}
    # Pass = at least 80% script purity AND reference content present
    passed = purity >= 0.8 and cont >= 1.0
    return ScoredExample(
        example_id=ex.id, metrics=metrics,
        **{"pass": passed}, output_excerpt=out.output[:200],
    )


def _transliteration_scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    """Round-trip: ref_devanagari + ref_latin in metadata; accept either."""
    md = ex.metadata or {}
    deva = md.get("reference_devanagari") or ex.reference or ""
    latin = md.get("reference_latin")
    score = scoring.transliteration_round_trip(out.output, deva, latin)
    return ScoredExample(
        example_id=ex.id, metrics={"transliteration": score},
        **{"pass": score >= 1.0}, output_excerpt=out.output[:200],
    )


def _code_mix_scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    """Hinglish code-mix benchmark: target devanagari fraction in metadata; closer to target = better."""
    md = ex.metadata or {}
    target = float(md.get("target_cmi", 0.5))
    actual = scoring.code_mix_index(out.output)
    proximity = max(0.0, 1.0 - abs(target - actual) * 2)
    refs = ex.references or ([ex.reference] if ex.reference else [])
    cont = max((scoring.contains(out.output, r) for r in refs), default=0.0)
    metrics = {
        "code_mix_index": actual,
        "code_mix_proximity": proximity,
        "contains": cont,
    }
    passed = proximity >= 0.6 and cont >= 1.0
    return ScoredExample(
        example_id=ex.id, metrics=metrics,
        **{"pass": passed}, output_excerpt=out.output[:200],
    )


def _semantic_judge_scorer_factory(judge_client=None) -> Callable[[BenchmarkExample, ModelOutput], ScoredExample]:
    def _scorer(ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
        ref = ex.reference or (ex.references[0] if ex.references else "")
        score = scoring.semantic_judge_score(out.output, ref, judge_client=judge_client)
        return ScoredExample(
            example_id=ex.id, metrics={"semantic_judge": score},
            **{"pass": score >= 0.7}, output_excerpt=out.output[:200],
        )
    return _scorer


SCORERS: dict[str, BenchmarkScorer] = {
    "exact_match": BenchmarkScorer("exact_match", _exact_match_scorer, "exact_match"),
    "contains": BenchmarkScorer("contains", _contains_scorer, "contains"),
    "script_purity": BenchmarkScorer("script_purity", _script_purity_scorer, "script_purity",
                                      pass_threshold=0.8),
    "transliteration": BenchmarkScorer("transliteration", _transliteration_scorer, "transliteration"),
    "code_mix": BenchmarkScorer("code_mix", _code_mix_scorer, "code_mix_proximity",
                                  pass_threshold=0.6),
}


def get_semantic_judge_scorer(judge_client=None) -> BenchmarkScorer:
    return BenchmarkScorer(
        "semantic_judge",
        _semantic_judge_scorer_factory(judge_client),
        "semantic_judge",
        pass_threshold=0.7,
    )


def score_example(scorer_name: str, ex: BenchmarkExample, out: ModelOutput) -> ScoredExample:
    if scorer_name not in SCORERS:
        raise KeyError(f"Unknown scorer {scorer_name!r}; known: {sorted(SCORERS)}")
    return SCORERS[scorer_name].fn(ex, out)
