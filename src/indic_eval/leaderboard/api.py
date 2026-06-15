"""FastAPI leaderboard. POST /submit a Scorecard, GET /leaderboard for the ranked list.

Auth-stub: a token gate via the LEADERBOARD_TOKEN env var. If unset, submissions
are open. Real deployment: front this with Vercel + a per-user token table.
"""
from __future__ import annotations
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel

from ..models.types import Scorecard
from .store import LeaderboardStore, MemoryLeaderboardStore


class LeaderboardEntry(BaseModel):
    model_id: str
    model_provider: str
    overall_score: float
    submitted_at: str
    by_benchmark: dict[str, float]


def _rank(cards: list[Scorecard]) -> list[LeaderboardEntry]:
    """Take latest scorecard per (model_id, model_provider), rank by overall_score desc."""
    by_key: dict[tuple[str, str], Scorecard] = {}
    for c in cards:
        key = (c.model_id, c.model_provider)
        prior = by_key.get(key)
        if prior is None or c.timestamp > prior.timestamp:
            by_key[key] = c
    rows = [
        LeaderboardEntry(
            model_id=c.model_id, model_provider=c.model_provider,
            overall_score=c.overall_score, submitted_at=c.timestamp.isoformat(),
            by_benchmark={b.benchmark_id: b.primary_score for b in c.benchmarks},
        )
        for c in by_key.values()
    ]
    rows.sort(key=lambda r: r.overall_score, reverse=True)
    return rows


def build_app(store: Optional[LeaderboardStore] = None) -> FastAPI:
    store = store or MemoryLeaderboardStore()
    expected_token = os.getenv("LEADERBOARD_TOKEN")

    app = FastAPI(title="indic-eval leaderboard", version="0.1.0")

    def _check_auth(x_token: Optional[str]) -> None:
        if expected_token and x_token != expected_token:
            raise HTTPException(status_code=401, detail="invalid token")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/submit")
    async def submit(card: Scorecard, x_token: Optional[str] = Header(default=None)) -> dict:
        _check_auth(x_token)
        # Reject zero-benchmark or zero-example submissions; cheap anti-spam.
        if not card.benchmarks or sum(b.n_examples for b in card.benchmarks) == 0:
            raise HTTPException(status_code=400, detail="empty scorecard")
        store.submit(card)
        return {"ok": True, "rank_after_submit": _rank(store.all())}

    @app.get("/leaderboard")
    async def leaderboard() -> dict:
        return {"entries": [r.model_dump() for r in _rank(store.all())]}

    @app.get("/model/{model_id}")
    async def by_model(model_id: str) -> dict:
        cards = store.by_model(model_id)
        return {"history": [c.model_dump() for c in cards]}

    return app
