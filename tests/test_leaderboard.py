"""Leaderboard API + store tests."""
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from indic_eval.leaderboard.api import build_app
from indic_eval.leaderboard.store import MemoryLeaderboardStore, FileLeaderboardStore
from indic_eval.models.types import Scorecard, BenchmarkResult


def _card(model_id="claude", score=0.85) -> Scorecard:
    return Scorecard(
        model_id=model_id, model_provider="bedrock",
        timestamp=datetime.now(timezone.utc),
        benchmarks=[BenchmarkResult(
            benchmark_id="indic-script-fidelity-v1",
            benchmark_name="Indic Script Fidelity",
            primary_metric="script_purity",
            primary_score=score,
            metric_aggregates={"script_purity": score},
            n_examples=15, n_passed=int(15 * score), examples=[],
        )],
        overall_score=score,
    )


def test_memory_store_round_trip():
    store = MemoryLeaderboardStore()
    c = _card()
    store.submit(c)
    assert store.all() == [c]
    assert store.by_model("claude") == [c]


def test_file_store_round_trip(tmp_path):
    p = tmp_path / "lb.jsonl"
    store = FileLeaderboardStore(p)
    c = _card()
    store.submit(c)
    loaded = store.all()
    assert len(loaded) == 1
    assert loaded[0].model_id == "claude"


def test_health_endpoint():
    app = build_app(MemoryLeaderboardStore())
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_submit_and_leaderboard():
    store = MemoryLeaderboardStore()
    app = build_app(store)
    client = TestClient(app)
    payload = _card("claude", 0.9).model_dump(mode="json")
    r = client.post("/submit", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["rank_after_submit"][0]["model_id"] == "claude"

    # Submit a worse model — claude should still rank first
    client.post("/submit", json=_card("sarvam", 0.6).model_dump(mode="json"))
    leaderboard = client.get("/leaderboard").json()["entries"]
    assert leaderboard[0]["model_id"] == "claude"
    assert leaderboard[1]["model_id"] == "sarvam"


def test_only_latest_card_per_model_in_ranking():
    store = MemoryLeaderboardStore()
    app = build_app(store)
    client = TestClient(app)
    # Submit a low score, then a higher one for the same model.
    older = _card("claude", 0.5)
    older_dict = older.model_dump(mode="json")
    older_dict["timestamp"] = "2026-01-01T00:00:00+00:00"
    client.post("/submit", json=older_dict)
    newer = _card("claude", 0.9)
    newer_dict = newer.model_dump(mode="json")
    newer_dict["timestamp"] = "2026-06-15T00:00:00+00:00"
    client.post("/submit", json=newer_dict)
    leaderboard = client.get("/leaderboard").json()["entries"]
    assert len(leaderboard) == 1
    assert leaderboard[0]["overall_score"] == 0.9


def test_empty_scorecard_rejected():
    app = build_app(MemoryLeaderboardStore())
    client = TestClient(app)
    bad = _card().model_dump(mode="json")
    bad["benchmarks"] = []
    r = client.post("/submit", json=bad)
    assert r.status_code == 400


def test_auth_required_when_token_set(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_TOKEN", "secret")
    app = build_app(MemoryLeaderboardStore())
    client = TestClient(app)
    r = client.post("/submit", json=_card().model_dump(mode="json"))
    assert r.status_code == 401
    r2 = client.post("/submit", json=_card().model_dump(mode="json"),
                      headers={"X-Token": "secret"})
    assert r2.status_code == 200


def test_model_history_endpoint():
    store = MemoryLeaderboardStore()
    app = build_app(store)
    client = TestClient(app)
    client.post("/submit", json=_card("claude", 0.5).model_dump(mode="json"))
    client.post("/submit", json=_card("claude", 0.9).model_dump(mode="json"))
    history = client.get("/model/claude").json()["history"]
    assert len(history) == 2
