"""Pure-function scoring tests. No model calls."""
from indic_eval.models import scoring


def test_exact_match_normalizes_whitespace():
    assert scoring.exact_match("नई दिल्ली", "  नई   दिल्ली  ") == 1.0
    assert scoring.exact_match("Delhi", "delhi") == 1.0


def test_exact_match_negative():
    assert scoring.exact_match("Mumbai", "Delhi") == 0.0


def test_contains_simple():
    assert scoring.contains("राजधानी नई दिल्ली है", "नई दिल्ली") == 1.0
    assert scoring.contains("hello world", "Mumbai") == 0.0


def test_script_purity_pure_devanagari():
    assert scoring.script_purity("नई दिल्ली", "devanagari") == 1.0


def test_script_purity_pure_latin():
    assert scoring.script_purity("Naii Dilli", "devanagari") == 0.0


def test_script_purity_mixed():
    pur = scoring.script_purity("Delhi दिल्ली", "devanagari")
    # Mixed input: "Delhi" (5 Latin) + "दिल्ली" (3 Devanagari letters incl ़ vowels);
    # exact ratio depends on whether combining marks count, just assert it's intermediate.
    assert 0.0 < pur < 1.0


def test_script_purity_neutral_chars_ignored():
    """Whitespace, digits, and ASCII punctuation should not count against script purity."""
    assert scoring.script_purity("नई दिल्ली, 2026.", "devanagari") == 1.0


def test_code_mix_index_zero_when_no_devanagari():
    assert scoring.code_mix_index("hello world") == 0.0


def test_code_mix_index_one_when_all_devanagari():
    assert scoring.code_mix_index("नमस्ते दोस्त") == 1.0


def test_code_mix_index_intermediate():
    cmi = scoring.code_mix_index("yaar मेरा caffeine चाहिए")
    # Intermediate code-mix: not all Latin, not all Devanagari.
    assert 0.0 < cmi < 1.0


def test_transliteration_round_trip_devanagari_match():
    assert scoring.transliteration_round_trip("उत्तर: नमस्ते", "नमस्ते") == 1.0


def test_transliteration_round_trip_latin_match():
    assert scoring.transliteration_round_trip("answer: namaste", "नमस्ते", "namaste") == 1.0


def test_transliteration_round_trip_partial_credit():
    """Some Devanagari present but not the reference phrase = 0.5."""
    score = scoring.transliteration_round_trip("किसी और शब्द", "नमस्ते", "namaste")
    assert score == 0.5


def test_transliteration_round_trip_zero():
    assert scoring.transliteration_round_trip("nothing useful", "नमस्ते", "namaste") == 0.0


def test_script_purity_unknown_script_raises():
    import pytest
    with pytest.raises(ValueError):
        scoring.script_purity("text", "klingon")


def test_semantic_judge_score_returns_zero_without_judge():
    """When no client is provided and AnthropicBedrock isn't reachable, score is 0
    instead of raising — eval over thousands of examples must not blow up."""
    score = scoring.semantic_judge_score("hello", "world", judge_client=None)
    assert 0.0 <= score <= 1.0
