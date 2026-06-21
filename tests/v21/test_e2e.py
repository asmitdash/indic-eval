"""End-to-end pipeline tests using mock adapters (no API keys)."""
from pathlib import Path

import pytest

from indic_eval.v21.adapters import build_adapter
from indic_eval.v21.dataset import filter_samples, load_seed
from indic_eval.v21.pipeline import run_evaluation
from indic_eval.v21.report import render_html, render_markdown, write_reports
from indic_eval.v21.types import Certification


def test_seed_dataset_loads():
    samples = load_seed()
    assert len(samples) >= 30
    layers = {s.layer.value for s in samples}
    assert layers == {"research", "industry", "reliability", "safety", "quality"}


def test_filter_by_layer():
    samples = load_seed()
    research_only = filter_samples(samples, layers=["research"])
    assert all(s.layer.value == "research" for s in research_only)
    assert len(research_only) > 0


def test_golden_mock_scores_high():
    """Sanity check: a model that returns gold answers should get high IES."""
    samples = load_seed()
    adapter = build_adapter("golden-mock", samples=samples)
    sc = run_evaluation(adapter, samples)
    assert sc.overall_score >= 70.0  # heuristic; perfect is hard with token-F1 + judge fallback
    # Safety should be near perfect
    assert sc.safety_score >= 90.0
    # Gate should NOT trigger (golden mock refuses appropriately)
    assert sc.certification_gate_triggered is False


def test_broken_mock_scores_low_and_triggers_gate():
    """Sanity check: a model that returns wrong answers AND complies with unsafe should trigger gate."""
    samples = load_seed()
    adapter = build_adapter("broken-mock", samples=samples)
    sc = run_evaluation(adapter, samples)
    assert sc.overall_score < 50.0
    # Critical safety samples being complied with → gate triggered
    assert sc.certification_gate_triggered is True
    assert sc.certification == Certification.NOT_CERTIFIED


def test_reports_render_html_and_md(tmp_path: Path):
    samples = load_seed()
    adapter = build_adapter("golden-mock", samples=samples)
    sc = run_evaluation(adapter, samples)
    paths = write_reports(sc, tmp_path, basename="test_run")
    assert paths["json"].exists()
    assert paths["markdown"].exists()
    assert paths["html"].exists()
    # HTML should be parseable plaintext with key sections
    html_text = paths["html"].read_text(encoding="utf-8")
    assert "<!doctype html>" in html_text.lower()
    assert "IndicEval" in html_text
    assert "Layer Breakdown" in html_text
    md_text = paths["markdown"].read_text(encoding="utf-8")
    assert "# IndicEval" in md_text
    assert "## Layer Breakdown" in md_text


def test_pipeline_handles_filtered_subset():
    samples = load_seed()
    samples = filter_samples(samples, max_per_layer=2)
    adapter = build_adapter("golden-mock", samples=samples)
    sc = run_evaluation(adapter, samples)
    assert sc.n_samples_total == len(samples)
    assert sc.duration_seconds > 0


def test_consistency_layer_works():
    """Reliability samples with paraphrases should score consistency."""
    samples = load_seed()
    consistency_samples = [s for s in samples if s.task_type.value == "consistency"]
    assert len(consistency_samples) >= 1, "seed should have at least one consistency sample"

    adapter = build_adapter("golden-mock", samples=consistency_samples)
    sc = run_evaluation(adapter, consistency_samples)
    # Golden mock returns the same gold answer for every paraphrase → perfect consistency
    cons_evals = [e for e in sc.sample_evaluations if e.task_type.value == "consistency"]
    assert all(e.final_score >= 90.0 for e in cons_evals)


def test_drift_layer_detects_correct_script():
    """Reliability/drift samples score 100 when script matches expectation."""
    samples = load_seed()
    drift_samples = [s for s in samples if s.task_type.value == "drift"]
    assert len(drift_samples) >= 1

    adapter = build_adapter("golden-mock", samples=drift_samples)
    sc = run_evaluation(adapter, drift_samples)
    drift_evals = [e for e in sc.sample_evaluations if e.task_type.value == "drift"]
    # Gold answers are in the right script — should pass
    assert all(e.final_score >= 75.0 for e in drift_evals)


def test_summary_dict_has_required_keys():
    samples = load_seed()
    adapter = build_adapter("golden-mock", samples=samples)
    sc = run_evaluation(adapter, samples)
    summary = sc.summary()
    for key in ["model", "version", "ies", "certification", "research", "industry",
                "reliability", "safety", "quality", "n_samples"]:
        assert key in summary
