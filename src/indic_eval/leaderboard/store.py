"""Leaderboard persistence."""
from __future__ import annotations
import threading
from pathlib import Path
from typing import Optional, Protocol

from ..models.types import Scorecard


class LeaderboardStore(Protocol):
    def submit(self, card: Scorecard) -> None: ...
    def all(self) -> list[Scorecard]: ...
    def by_model(self, model_id: str) -> list[Scorecard]: ...


class MemoryLeaderboardStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._cards: list[Scorecard] = []

    def submit(self, card: Scorecard) -> None:
        with self._lock:
            self._cards.append(card)

    def all(self) -> list[Scorecard]:
        with self._lock:
            return list(self._cards)

    def by_model(self, model_id: str) -> list[Scorecard]:
        with self._lock:
            return [c for c in self._cards if c.model_id == model_id]


class FileLeaderboardStore:
    """One JSON-Lines file holds all submissions. Append-only."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def submit(self, card: Scorecard) -> None:
        line = card.model_dump_json() + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)

    def all(self) -> list[Scorecard]:
        if not self.path.exists():
            return []
        out: list[Scorecard] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(Scorecard.model_validate_json(line))
                except Exception:
                    continue
        return out

    def by_model(self, model_id: str) -> list[Scorecard]:
        return [c for c in self.all() if c.model_id == model_id]
