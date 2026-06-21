"""V7 §10 normalization pipeline tests."""
from indic_eval.v21.normalization import normalize_indic, tokens


def test_idempotent():
    s = "  नई दिल्ली। "
    assert normalize_indic(normalize_indic(s)) == normalize_indic(s)


def test_strip_zwj_zwnj():
    s_with_zwj = "क‍ष"
    s_clean = "कष"
    assert normalize_indic(s_with_zwj) == normalize_indic(s_clean)


def test_strip_trailing_danda():
    assert normalize_indic("नई दिल्ली।") == normalize_indic("नई दिल्ली")
    assert normalize_indic("नई दिल्ली॥") == normalize_indic("नई दिल्ली")


def test_strip_trailing_punct_english():
    assert normalize_indic("Mumbai!!!") == normalize_indic("Mumbai")
    assert normalize_indic("Mumbai.") == normalize_indic("Mumbai")


def test_lowercase():
    assert normalize_indic("MUMBAI") == "mumbai"
    assert normalize_indic("Mumbai") == "mumbai"


def test_collapse_whitespace():
    assert normalize_indic("a  b   c\nd\te") == "a b c d e"


def test_nfc_canonicalization():
    # combining characters get composed under NFC
    composed = "क"     # U+0915
    assert normalize_indic(composed) == "क"


def test_tokens_whitespace():
    assert tokens("  hello   world  ") == ["hello", "world"]
    assert tokens("नई दिल्ली") == ["नई", "दिल्ली"]


def test_empty_string():
    assert normalize_indic("") == ""
    assert normalize_indic("   ") == ""
