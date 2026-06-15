"""Harness end-to-end with deterministic adapters."""
from indic_eval.benchmarks.loader import load_all, BENCHMARK_REGISTRY
from indic_eval.benchmarks.adapters import EchoAdapter, ScriptedAdapter
from indic_eval.harness.runner import run_benchmark, run_all


def test_echo_adapter_passes_when_reference_in_prompt():
    """Sanity: an EchoAdapter on a contains-scored benchmark should pass any example
    where the reference is literally in the prompt."""
    benchmarks = {b.id: b for b in load_all()}
    diglossia = benchmarks["indic-diglossia-formal-v1"]
    # The diglossia prompts include the reference word verbatim in some cases.
    # We pick contains scoring which reflects that expectation.
    result = run_benchmark(EchoAdapter(), diglossia, scorer_name="contains", max_examples=5)
    assert result.n_examples == 5
    # Echo should pass any example where the reference word appears in the prompt.
    # Not all do — the metric just needs to be a valid float.
    assert 0.0 <= result.primary_score <= 1.0


def test_scripted_adapter_perfect_score():
    """Scripted adapter that always returns the reference word should pass on contains."""
    benchmarks = {b.id: b for b in load_all()}
    bho = benchmarks["indic-dialect-bhojpuri-v1"]
    # Script the adapter so every prompt returns the first reference of that example.
    scripted_map = {}
    for ex in bho.examples:
        # Use the prompt as the lookup key, return the reference.
        ref = (ex.references or [ex.reference or ""])[0]
        scripted_map[ex.prompt] = f"उत्तर: {ref} धन्यवाद"
    adapter = ScriptedAdapter(model_id="oracle", scripted=scripted_map, default="")
    result = run_benchmark(adapter, bho, scorer_name="contains")
    assert result.primary_score == 1.0
    assert result.n_passed == result.n_examples


def test_scripted_adapter_zero_score():
    """Scripted adapter returning unrelated text should score 0."""
    benchmarks = {b.id: b for b in load_all()}
    bho = benchmarks["indic-dialect-bhojpuri-v1"]
    adapter = ScriptedAdapter(model_id="bad", scripted={}, default="hello world")
    result = run_benchmark(adapter, bho, scorer_name="contains")
    assert result.primary_score == 0.0
    assert result.n_passed == 0


def test_run_all_produces_scorecard():
    benchmarks = load_all()
    adapter = ScriptedAdapter(model_id="dummy", scripted={}, default="नमस्ते दोस्त")
    card = run_all(adapter, benchmarks, scorer_for=BENCHMARK_REGISTRY)
    assert card.model_id == "dummy"
    assert len(card.benchmarks) == 5
    assert 0.0 <= card.overall_score <= 1.0
    summary = card.to_summary()
    assert summary["model"] == "dummy"
    assert "by_benchmark" in summary


def test_run_all_with_weights():
    benchmarks = load_all()
    adapter = ScriptedAdapter(model_id="dummy", scripted={}, default="नई दिल्ली नमस्ते")
    weights = {"indic-script-fidelity-v1": 2.0, "indic-dialect-bhojpuri-v1": 0.5}
    card = run_all(adapter, benchmarks, scorer_for=BENCHMARK_REGISTRY, weights=weights)
    assert card.overall_score >= 0.0


def test_adapter_exception_is_recorded_not_raised():
    """If an adapter raises mid-run, the harness records it as an error example
    rather than crashing the run."""
    class BoomAdapter:
        model_id = "boom"; provider = "test"
        def generate(self, prompt, **kwargs):
            raise RuntimeError("simulated failure")

    benchmarks = {b.id: b for b in load_all()}
    b = benchmarks["indic-script-fidelity-v1"]
    result = run_benchmark(BoomAdapter(), b, scorer_name="exact_match", max_examples=3)
    assert result.n_examples == 3
    assert result.n_passed == 0
    for s in result.examples:
        assert s.output_excerpt.startswith("<error:")
