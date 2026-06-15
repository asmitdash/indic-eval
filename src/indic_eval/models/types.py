"""Core schemas for the eval harness.

Why explicit ScoredExample / Scorecard objects? Because the moat is reproducibility.
The user submits a model adapter, runs benchmarks, and gets a deterministic JSON
artefact that survives a code review. No hidden global state.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Protocol
from pydantic import BaseModel, Field


class Language(str, Enum):
    HI = "hi"      # Hindi
    BN = "bn"      # Bengali
    TA = "ta"      # Tamil
    TE = "te"      # Telugu
    MR = "mr"      # Marathi
    GU = "gu"      # Gujarati
    KN = "kn"      # Kannada
    ML = "ml"      # Malayalam
    PA = "pa"      # Punjabi
    OR = "or"      # Odia
    AS = "as"      # Assamese
    EN = "en"      # English (control)
    HI_EN = "hi-en"  # Hinglish (code-mixed)
    BHO = "bho"    # Bhojpuri (low-resource Hindi-family)
    AWA = "awa"    # Awadhi (low-resource Hindi-family)
    MAG = "mag"    # Magahi (low-resource Hindi-family)


class Script(str, Enum):
    LATIN = "latin"
    DEVANAGARI = "devanagari"
    BENGALI = "bengali"
    TAMIL = "tamil"
    TELUGU = "telugu"
    GURMUKHI = "gurmukhi"
    GUJARATI = "gujarati"
    KANNADA = "kannada"
    MALAYALAM = "malayalam"
    ODIA = "odia"
    MIXED = "mixed"


class BenchmarkExample(BaseModel):
    """One row of a benchmark dataset."""

    id: str
    prompt: str = Field(description="Input handed to the model under test")
    reference: Optional[str] = Field(default=None, description="Reference output for exact-match / contains scoring")
    references: list[str] = Field(default_factory=list, description="Multiple acceptable references")
    language: Language
    script: Optional[Script] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Benchmark(BaseModel):
    """A named benchmark — a list of examples + a scoring rubric."""

    id: str
    name: str
    description: str
    primary_metric: str = Field(description="Which metric in the scorecard is the headline number")
    examples: list[BenchmarkExample]


class ModelOutput(BaseModel):
    """One output from the model under test, mirroring a single BenchmarkExample."""

    example_id: str
    output: str
    latency_ms: int = 0
    cost_usd: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoredExample(BaseModel):
    """A single example after scoring."""

    example_id: str
    metrics: dict[str, float]
    pass_: bool = Field(alias="pass")  # 'pass' is a Python keyword
    output_excerpt: str = ""

    model_config = {"populate_by_name": True}


class BenchmarkResult(BaseModel):
    benchmark_id: str
    benchmark_name: str
    primary_metric: str
    primary_score: float
    metric_aggregates: dict[str, float]
    n_examples: int
    n_passed: int
    examples: list[ScoredExample]


class Scorecard(BaseModel):
    """The persistent artefact of a single eval run."""

    model_id: str
    model_provider: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    benchmarks: list[BenchmarkResult]
    overall_score: float = Field(description="Weighted mean of benchmark primary scores")
    notes: str = ""

    def to_summary(self) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "overall": round(self.overall_score, 4),
            "by_benchmark": {
                b.benchmark_id: round(b.primary_score, 4) for b in self.benchmarks
            },
            "n_examples": sum(b.n_examples for b in self.benchmarks),
        }


class ModelAdapter(Protocol):
    """Plug an LLM into the harness. Implement this to add a new model."""

    model_id: str
    provider: str

    def generate(self, prompt: str, **kwargs: Any) -> str: ...
