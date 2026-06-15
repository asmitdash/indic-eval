"""Observability SDK + detectors."""
from indic_eval.observability import (
    LogEntry, MemoryLogStore, FileLogStore, Tracer,
    EmptyResponseDetector, ScriptSwitchDetector, HallucinationHeuristicDetector,
    DriftDetector, RunDetectors,
)


def _make_entry(deployment="bot", **overrides) -> LogEntry:
    base = dict(
        deployment=deployment, model_id="claude-opus-4-7", provider="bedrock",
        prompt="hi", output="hello",
    )
    base.update(overrides)
    return LogEntry(**base)


def test_memory_store_round_trip():
    store = MemoryLogStore()
    e = _make_entry()
    store.append(e)
    assert store.recent("bot", n=10) == [e]
    assert store.all() == [e]


def test_memory_store_filters_by_deployment():
    store = MemoryLogStore()
    store.append(_make_entry(deployment="a"))
    store.append(_make_entry(deployment="b"))
    assert len(store.recent("a", 10)) == 1
    assert len(store.recent("b", 10)) == 1


def test_memory_store_caps_at_max():
    store = MemoryLogStore(max_entries=3)
    for i in range(5):
        store.append(_make_entry(prompt=f"p{i}"))
    assert len(store.all()) == 3


def test_file_store_round_trip(tmp_path):
    store = FileLogStore(tmp_path / "logs")
    e = _make_entry(deployment="acme")
    store.append(e)
    loaded = store.recent("acme", n=10)
    assert len(loaded) == 1
    assert loaded[0].id == e.id
    assert loaded[0].prompt == e.prompt


def test_tracer_span_records_latency_and_output():
    store = MemoryLogStore()
    tracer = Tracer(deployment="t", model_id="m", store=store, provider="test")
    with tracer.span("hello world", language_hint="hi") as s:
        s.set_output("नमस्ते")
        s.set_cost(0.001)
    entries = store.recent("t", 10)
    assert len(entries) == 1
    assert entries[0].output == "नमस्ते"
    assert entries[0].latency_ms >= 0
    assert entries[0].cost_usd == 0.001
    assert entries[0].language_hint == "hi"


def test_tracer_records_exception_in_metadata():
    store = MemoryLogStore()
    tracer = Tracer(deployment="t", model_id="m", store=store)
    try:
        with tracer.span("hello") as s:
            s.set_output("partial")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    entries = store.recent("t", 10)
    assert len(entries) == 1
    assert "boom" in entries[0].metadata.get("error", "")


def test_empty_response_detector_fires():
    entries = [_make_entry(output="" if i < 5 else "ok") for i in range(20)]
    alerts = EmptyResponseDetector(threshold=0.1).run(entries)
    assert len(alerts) == 1
    assert "rate" in alerts[0].metadata


def test_empty_response_detector_silent_below_threshold():
    entries = [_make_entry(output="" if i == 0 else "ok") for i in range(100)]
    alerts = EmptyResponseDetector(threshold=0.05).run(entries)
    assert alerts == []


def test_script_switch_detector_fires_on_latin_output_for_hi():
    entries = [_make_entry(output="Delhi is the capital", language_hint="hi") for _ in range(10)]
    alerts = ScriptSwitchDetector().run(entries)
    assert len(alerts) == 1
    assert "script-switch" in alerts[0].message.lower()


def test_script_switch_detector_silent_on_devanagari():
    entries = [_make_entry(output="नई दिल्ली राजधानी है", language_hint="hi") for _ in range(10)]
    alerts = ScriptSwitchDetector().run(entries)
    assert alerts == []


def test_hallucination_heuristic_picks_up_hedging():
    entries = [
        _make_entry(output="According to my training data, ..."),
        _make_entry(output="Normal response"),
    ]
    alerts = HallucinationHeuristicDetector().run(entries)
    assert len(alerts) == 1


def test_drift_detector_fires_when_latency_doubles():
    entries = [_make_entry(latency_ms=100) for _ in range(200)]
    entries += [_make_entry(latency_ms=400) for _ in range(50)]
    alerts = DriftDetector(baseline_size=200, recent_size=50).run(entries)
    assert len(alerts) == 1
    assert alerts[0].severity in ("warn", "critical")


def test_drift_detector_silent_with_too_few_entries():
    entries = [_make_entry(latency_ms=100) for _ in range(10)]
    alerts = DriftDetector(baseline_size=200, recent_size=50).run(entries)
    assert alerts == []


def test_run_detectors_aggregates_and_isolates_failures():
    class BoomDetector:
        name = "boom"
        def run(self, entries):
            raise RuntimeError("oops")
    entries = [_make_entry(output="" if i < 5 else "ok") for i in range(20)]
    runner = RunDetectors([EmptyResponseDetector(threshold=0.1), BoomDetector()])
    alerts = runner.run(entries)
    # One from EmptyResponseDetector (rate=0.25), one critical from BoomDetector.
    detector_names = {a.detector for a in alerts}
    assert "empty_response" in detector_names
    assert "boom" in detector_names
