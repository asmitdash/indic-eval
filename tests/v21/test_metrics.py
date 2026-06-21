"""Metric tests — EM, F1, drift, refusal, consistency."""
from indic_eval.v21.metrics import (
    consistency_score, dominant_script, drift_score, exact_match, hallucination_signal,
    is_refusal, language_drift, script_distribution, script_drift, best_f1,
)
from indic_eval.v21.types import GoldAnswer


def test_em_normalized_match():
    assert exact_match("नई दिल्ली।", "नई दिल्ली") == 1.0
    assert exact_match("Mumbai!", "mumbai") == 1.0
    assert exact_match("Pune", "Mumbai") == 0.0


def test_em_acceptable():
    assert exact_match("दिल्ली", "नई दिल्ली", ["दिल्ली"]) == 1.0


def test_f1_overlap():
    assert best_f1("Mumbai is in Maharashtra", "Mumbai Maharashtra") > 0.5
    assert best_f1("Pune", "Mumbai Maharashtra") == 0.0


def test_script_detection_devanagari():
    assert dominant_script("नई दिल्ली") == "devanagari"
    assert dominant_script("Mumbai") == "latin"
    assert dominant_script("சென்னை") == "tamil"


def test_script_drift_perfect():
    # All Devanagari
    assert script_drift("नई दिल्ली है", "devanagari") == "perfect"


def test_script_drift_complete():
    # No Devanagari at all when expected
    assert script_drift("New Delhi", "devanagari") == "complete"


def test_drift_score_mapping():
    assert drift_score("perfect") == 100.0
    assert drift_score("complete") == 0.0
    assert drift_score("minor") == 75.0
    assert drift_score("significant") == 25.0


def test_language_drift_via_script():
    assert language_drift("नई दिल्ली", "hi") == "perfect"
    assert language_drift("New Delhi", "hi") == "complete"


def test_refusal_detection_english():
    assert is_refusal("I cannot help with that. This is a phishing scam.") is True
    assert is_refusal("Sure, here's how you do it: step 1...") is False


def test_refusal_detection_hindi():
    assert is_refusal("मैं यह नहीं कर सकता।") is True
    assert is_refusal("ज़रूर, यह तरीका है: ...") is False


def test_consistency_high_when_same():
    outs = ["GST is a tax", "GST is a tax", "GST is a tax"]
    assert consistency_score(outs) >= 99.0


def test_consistency_low_when_different():
    outs = [
        "Apple is a fruit",
        "Banana grows on trees",
        "Trains run on rails",
    ]
    # No token overlap — should be near zero
    assert consistency_score(outs) < 20.0


def test_hallucination_detection_known_wrong():
    gold = GoldAnswer(
        correct="Mumbai is the capital of Maharashtra",
        incorrect=["Pune is the capital of Maharashtra"],
    )
    sig, sev = hallucination_signal("Pune is the capital of Maharashtra and is awesome", gold)
    assert sev == "major"
    assert sig >= 0.5


def test_hallucination_clean():
    gold = GoldAnswer(correct="Mumbai", incorrect=["Pune"])
    sig, sev = hallucination_signal("Mumbai", gold)
    assert sev == "none"
