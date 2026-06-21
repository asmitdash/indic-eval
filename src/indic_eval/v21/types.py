"""v2.1 core types — Samples, Predictions, Scores, Scorecards, Reports.

All schemas here are normative: they implement V6 §5 sample schema
and V7 §32 leaderboard schema.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# Enums (closed value sets — keep in sync with the spec)
# ----------------------------------------------------------------------

class Layer(str, Enum):
    RESEARCH = "research"
    INDUSTRY = "industry"
    RELIABILITY = "reliability"
    SAFETY = "safety"
    QUALITY = "quality"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Visibility(str, Enum):
    PUBLIC = "public"
    HIDDEN = "hidden"


class Severity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class Certification(str, Enum):
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"
    NOT_CERTIFIED = "Not Certified"


class TaskType(str, Enum):
    QA = "qa"
    READING_COMPREHENSION = "reading_comprehension"
    CLASSIFICATION = "classification"
    INFORMATION_EXTRACTION = "information_extraction"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    WORKFLOW = "workflow"          # industry workflows
    REFUSAL = "refusal"             # safety refusal expected
    JUDGE = "judge"                 # quality, judge-scored
    CONSISTENCY = "consistency"     # reliability paraphrase set
    DRIFT = "drift"                 # language/script drift


# ----------------------------------------------------------------------
# Sample (V6 §5)
# ----------------------------------------------------------------------

class GoldAnswer(BaseModel):
    """V6 §26 gold answer schema."""
    correct: str = ""
    acceptable: list[str] = Field(default_factory=list)
    incorrect: list[str] = Field(default_factory=list)


class Sample(BaseModel):
    """V6 §5 sample metadata schema."""
    id: str
    benchmark_version: str = "2.1"
    layer: Layer
    track: str = "model"               # model | agent | rag | system
    domain: str                          # finance | government | legal | ...
    language: str                        # ISO code: hi, mr, en, hi-en (code-mix), ...
    difficulty: Difficulty
    task_type: TaskType
    visibility: Visibility = Visibility.PUBLIC
    source: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    rubric_id: str = ""

    question: str
    gold: GoldAnswer

    # Layer-specific extras
    paraphrases: list[str] = Field(default_factory=list)   # for consistency tests
    expected_language: Optional[str] = None                 # for language drift
    expected_script: Optional[str] = None                   # for script drift
    refusal_expected: bool = False                          # for safety
    safety_severity_if_complies: Severity = Severity.NONE  # gate trigger

    # Reviewer metadata (V6 §25)
    reviewer_1: str = ""
    reviewer_2: str = ""
    iaa_kappa: float = 1.0


# ----------------------------------------------------------------------
# Model interaction
# ----------------------------------------------------------------------

class Prediction(BaseModel):
    """One model output for one sample (or paraphrase)."""
    sample_id: str
    output: str
    latency_ms: float = 0.0
    error: Optional[str] = None


# ----------------------------------------------------------------------
# Per-sample evaluation
# ----------------------------------------------------------------------

class SampleEvaluation(BaseModel):
    """One sample's score after metric + penalty application."""
    sample_id: str
    layer: Layer
    domain: str
    language: str
    difficulty: Difficulty
    task_type: TaskType

    raw_score: float                  # 0-100, before penalty
    severity: Severity = Severity.NONE
    penalty: float = 0.0              # subtracted from raw
    final_score: float                # max(0, raw - penalty)

    metric_breakdown: dict[str, float | str] = Field(default_factory=dict)
    notes: str = ""
    output_sample: str = ""           # truncated model output for report
    gold_sample: str = ""             # truncated gold for report
    triggers_certification_gate: bool = False


# ----------------------------------------------------------------------
# Layer aggregate
# ----------------------------------------------------------------------

class LayerScore(BaseModel):
    layer: Layer
    score: float                      # 0-100, floored
    n_samples: int
    n_passed: int                     # final_score >= 70
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    sub_scores: dict[str, float] = Field(default_factory=dict)


# ----------------------------------------------------------------------
# Final scorecard (V5 §25 + §32)
# ----------------------------------------------------------------------

class Scorecard(BaseModel):
    model_name: str
    model_vendor: str = ""
    model_version: str = ""
    benchmark_version: str = "2.1"
    judge_mode: str = "dev"             # dev | prod

    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    research_score: float = 0.0
    industry_score: float = 0.0
    reliability_score: float = 0.0
    safety_score: float = 0.0
    quality_score: float = 0.0

    overall_score: float = 0.0          # IES (V7 §2)
    confidence_interval: tuple[float, float] = (0.0, 0.0)

    certification: Certification = Certification.NOT_CERTIFIED
    certification_gate_triggered: bool = False
    gate_triggers: list[str] = Field(default_factory=list)  # list of sample_ids that triggered

    layer_scores: dict[str, LayerScore] = Field(default_factory=dict)
    sample_evaluations: list[SampleEvaluation] = Field(default_factory=list)

    # Operational
    n_samples_total: int = 0
    n_samples_failed_to_run: int = 0
    duration_seconds: float = 0.0
    cost_estimate_usd: float = 0.0

    notes: str = ""

    def summary(self) -> dict:
        return {
            "model": self.model_name,
            "version": self.benchmark_version,
            "ies": round(self.overall_score, 2),
            "ci": [round(self.confidence_interval[0], 2), round(self.confidence_interval[1], 2)],
            "certification": self.certification.value,
            "gated": self.certification_gate_triggered,
            "research": round(self.research_score, 2),
            "industry": round(self.industry_score, 2),
            "reliability": round(self.reliability_score, 2),
            "safety": round(self.safety_score, 2),
            "quality": round(self.quality_score, 2),
            "n_samples": self.n_samples_total,
            "duration_s": round(self.duration_seconds, 1),
        }
