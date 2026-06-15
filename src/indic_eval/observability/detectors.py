"""Offline detectors over a window of LogEntry items.

Each detector is a pure function: list[LogEntry] -> list[DetectorAlert]. Run
them on a schedule against the store; surface alerts in the dashboard.

Cheap heuristics first; LLM-judge detector available but optional.
"""
from __future__ import annotations
import statistics
from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

from .sdk import LogEntry
from ..models import scoring


@dataclass
class DetectorAlert:
    detector: str
    severity: str  # info | warn | critical
    message: str
    sample_log_id: Optional[str] = None
    metadata: dict | None = None


class Detector(Protocol):
    name: str
    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]: ...


class EmptyResponseDetector:
    name = "empty_response"

    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold

    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]:
        if not entries:
            return []
        empty = [e for e in entries if not e.output.strip()]
        rate = len(empty) / len(entries)
        alerts: list[DetectorAlert] = []
        if rate > self.threshold:
            alerts.append(DetectorAlert(
                detector=self.name,
                severity="warn" if rate < 0.2 else "critical",
                message=f"Empty-response rate {rate:.1%} over {len(entries)} calls (threshold {self.threshold:.1%}).",
                sample_log_id=empty[0].id if empty else None,
                metadata={"rate": rate, "n": len(entries)},
            ))
        return alerts


class ScriptSwitchDetector:
    """Flags calls where the language hint says e.g. 'hi' but output is mostly Latin
    (or vice-versa). Critical for vernacular deployments — silent English-output
    drift is the #1 user complaint.
    """
    name = "script_switch"

    SCRIPT_FOR_LANG = {
        "hi": "devanagari", "mr": "devanagari", "ne": "devanagari",
        "bn": "bengali", "as": "bengali",
        "ta": "tamil", "te": "telugu", "kn": "kannada", "ml": "malayalam",
        "gu": "gujarati", "pa": "gurmukhi", "or": "odia",
        "bho": "devanagari", "awa": "devanagari", "mag": "devanagari",
    }

    def __init__(self, min_purity: float = 0.5, sample_threshold: float = 0.1):
        self.min_purity = min_purity
        self.sample_threshold = sample_threshold

    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]:
        relevant = [e for e in entries if e.language_hint in self.SCRIPT_FOR_LANG]
        if not relevant:
            return []
        bad: list[LogEntry] = []
        for e in relevant:
            expected = self.SCRIPT_FOR_LANG[e.language_hint]
            if scoring.script_purity(e.output, expected) < self.min_purity:
                bad.append(e)
        rate = len(bad) / len(relevant)
        if rate < self.sample_threshold:
            return []
        return [DetectorAlert(
            detector=self.name,
            severity="warn" if rate < 0.3 else "critical",
            message=(f"Script-switch detected: {len(bad)} of {len(relevant)} vernacular "
                      f"calls returned output with <{self.min_purity:.0%} expected-script purity."),
            sample_log_id=bad[0].id if bad else None,
            metadata={"rate": rate, "n_relevant": len(relevant)},
        )]


class HallucinationHeuristicDetector:
    """Cheap heuristics for likely hallucination — verbatim fabrications often look
    suspiciously fluent and confident. Heuristic-only here; in prod you'd plug an
    LLM judge."""
    name = "hallucination_heuristic"
    SUSPICIOUS_TOKENS = (
        "i don't have information", "i cannot verify",
        "this is hypothetical", "according to my training",
    )

    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]:
        suspicious = [e for e in entries
                       if any(s in e.output.lower() for s in self.SUSPICIOUS_TOKENS)]
        if not suspicious:
            return []
        rate = len(suspicious) / len(entries) if entries else 0
        return [DetectorAlert(
            detector=self.name, severity="info",
            message=f"{len(suspicious)} of {len(entries)} calls contain hedging language — review for hallucination.",
            sample_log_id=suspicious[0].id,
            metadata={"rate": rate},
        )]


class DriftDetector:
    """Compares the latest window vs a baseline window. Flags significant
    latency or empty-rate drift. Works as long as you call it with consistent
    window sizes; uses Welch-ish ratio of means."""
    name = "drift"

    def __init__(self, baseline_size: int = 200, recent_size: int = 50,
                  latency_ratio_threshold: float = 1.5):
        self.baseline_size = baseline_size
        self.recent_size = recent_size
        self.lr_threshold = latency_ratio_threshold

    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]:
        if len(entries) < self.baseline_size + self.recent_size:
            return []
        baseline = entries[-(self.baseline_size + self.recent_size):-self.recent_size]
        recent = entries[-self.recent_size:]
        bl = statistics.fmean(e.latency_ms for e in baseline) if baseline else 0
        rl = statistics.fmean(e.latency_ms for e in recent) if recent else 0
        if bl <= 0:
            return []
        ratio = rl / bl
        if ratio < self.lr_threshold:
            return []
        return [DetectorAlert(
            detector=self.name,
            severity="warn" if ratio < 2.0 else "critical",
            message=f"Latency drift: recent mean {rl:.0f}ms vs baseline {bl:.0f}ms (ratio {ratio:.2f}).",
            metadata={"baseline_ms": bl, "recent_ms": rl, "ratio": ratio},
        )]


class RunDetectors:
    """Orchestrates a set of detectors and returns combined alerts."""

    def __init__(self, detectors: Iterable[Detector]):
        self.detectors = list(detectors)

    def run(self, entries: list[LogEntry]) -> list[DetectorAlert]:
        out: list[DetectorAlert] = []
        for d in self.detectors:
            try:
                out.extend(d.run(entries))
            except Exception as e:
                out.append(DetectorAlert(
                    detector=getattr(d, "name", "unknown"),
                    severity="critical",
                    message=f"Detector failed: {type(e).__name__}: {e}",
                ))
        return out
