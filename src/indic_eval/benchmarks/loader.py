"""Load benchmark JSON files."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models.types import Benchmark, BenchmarkExample


def default_benchmark_root() -> Path:
    return Path(__file__).resolve().parent / "data"


def load_benchmark(path: str | Path) -> Benchmark:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    examples = [BenchmarkExample.model_validate(e) for e in raw.get("examples", [])]
    return Benchmark(
        id=raw["id"], name=raw["name"], description=raw.get("description", ""),
        primary_metric=raw.get("primary_metric", "exact_match"),
        examples=examples,
    )


@lru_cache(maxsize=1)
def load_all(root: Optional[Path] = None) -> list[Benchmark]:
    root = root or default_benchmark_root()
    out: list[Benchmark] = []
    for p in sorted(root.glob("*.json")):
        out.append(load_benchmark(p))
    return out


# Default scorer per benchmark id — referenced by run_all if not overridden.
BENCHMARK_REGISTRY: dict[str, str] = {
    "indic-script-fidelity-v1": "script_purity",
    "indic-transliteration-v1": "transliteration",
    "indic-code-mix-hinglish-v1": "code_mix",
    "indic-diglossia-formal-v1": "contains",
    "indic-dialect-bhojpuri-v1": "contains",
}
