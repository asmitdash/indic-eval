"""Dataset loader — reads seed_v21.json (and other versioned datasets) into Sample objects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .types import GoldAnswer, Sample, Severity


_DATA_DIR = Path(__file__).resolve().parent / "data"


def load_seed() -> list[Sample]:
    """Load the v2.1 seed dataset (~120 samples).

    Combines `seed_v21.json` (the original 40) and `seed_v21_extra.json`
    (~80 expansion samples). Both files use the same schema.
    """
    samples = list(load_from_file(_DATA_DIR / "seed_v21.json"))
    extra = _DATA_DIR / "seed_v21_extra.json"
    if extra.is_file():
        samples.extend(load_from_file(extra))
    return samples


def load_from_file(path: Path | str) -> list[Sample]:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    samples = []
    for item in raw["samples"]:
        gold_raw = item["gold"]
        gold = GoldAnswer(
            correct=gold_raw.get("correct", ""),
            acceptable=gold_raw.get("acceptable", []),
            incorrect=gold_raw.get("incorrect", []),
        )
        sev = item.get("safety_severity_if_complies", "none")
        sample = Sample(
            id=item["id"],
            layer=item["layer"],
            domain=item["domain"],
            language=item["language"],
            difficulty=item["difficulty"],
            task_type=item["task_type"],
            question=item["question"],
            gold=gold,
            paraphrases=item.get("paraphrases", []),
            expected_language=item.get("expected_language"),
            expected_script=item.get("expected_script"),
            refusal_expected=item.get("refusal_expected", False),
            safety_severity_if_complies=Severity(sev),
        )
        samples.append(sample)
    return samples


def filter_samples(samples: list[Sample],
                   layers: Optional[list[str]] = None,
                   languages: Optional[list[str]] = None,
                   max_per_layer: Optional[int] = None) -> list[Sample]:
    out = list(samples)
    if layers:
        layers = [l.lower() for l in layers]
        out = [s for s in out if s.layer.value in layers]
    if languages:
        languages = [l.lower() for l in languages]
        out = [s for s in out if s.language.lower() in languages]
    if max_per_layer:
        per_layer: dict[str, int] = {}
        keep = []
        for s in out:
            k = s.layer.value
            if per_layer.get(k, 0) < max_per_layer:
                keep.append(s)
                per_layer[k] = per_layer.get(k, 0) + 1
        out = keep
    return out
