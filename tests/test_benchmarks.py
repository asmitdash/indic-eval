"""Benchmarks load + are well-formed."""
from indic_eval.benchmarks.loader import load_all, BENCHMARK_REGISTRY
from indic_eval.harness.scorers import SCORERS


def test_all_benchmarks_load():
    benchmarks = load_all()
    assert len(benchmarks) == 5
    ids = {b.id for b in benchmarks}
    assert {
        "indic-script-fidelity-v1",
        "indic-transliteration-v1",
        "indic-code-mix-hinglish-v1",
        "indic-diglossia-formal-v1",
        "indic-dialect-bhojpuri-v1",
    } == ids


def test_each_benchmark_has_examples():
    for b in load_all():
        assert len(b.examples) >= 10, f"{b.id} has only {len(b.examples)} examples"
        for ex in b.examples:
            assert ex.id, f"empty id in {b.id}"
            assert ex.prompt, f"empty prompt in {b.id}/{ex.id}"


def test_every_benchmark_has_a_registered_scorer():
    for b in load_all():
        scorer_name = BENCHMARK_REGISTRY.get(b.id)
        assert scorer_name is not None, f"{b.id} not in BENCHMARK_REGISTRY"
        assert scorer_name in SCORERS, f"{b.id} -> {scorer_name} not in SCORERS"


def test_no_duplicate_example_ids_within_benchmark():
    for b in load_all():
        ids = [ex.id for ex in b.examples]
        assert len(ids) == len(set(ids)), f"duplicate ids in {b.id}"


def test_dialect_benchmark_includes_low_resource_languages():
    benchmarks = {b.id: b for b in load_all()}
    bho = benchmarks["indic-dialect-bhojpuri-v1"]
    languages = {ex.language.value for ex in bho.examples}
    assert "bho" in languages or "awa" in languages or "mag" in languages
