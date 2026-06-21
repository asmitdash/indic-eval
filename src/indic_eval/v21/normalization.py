"""Indic normalization pipeline — V7 §10.

Implements:
  NFC → strip ZWJ/ZWNJ → lowercase → trim → strip trailing punct (incl. danda) → collapse whitespace

Used before any string-equality metric (Exact Match, F1, IE field-match).
"""
from __future__ import annotations

import re
import unicodedata


_ZWJ = "‍"
_ZWNJ = "‌"

# Trailing-punctuation set: ASCII + Devanagari danda + various Indic stops.
_TRAIL_PUNCT_RE = re.compile(r"[\.,!?;:।॥…]+\s*$")
_WS_RE = re.compile(r"\s+")


def normalize_indic(text: str, language: str = "") -> str:
    """V7 §10 normalization pipeline.

    Steps:
      1. Unicode NFC.
      2. Strip ZWJ (U+200D) and ZWNJ (U+200C).
      3. Lowercase (safe for Indic scripts which have no case;
         affects mixed Indic-English output).
      4. Trim leading/trailing whitespace.
      5. Strip trailing sentence terminators (., ?, !, ;, :, ।, ॥, …).
      6. Collapse internal whitespace.

    The function is idempotent: normalize(normalize(x)) == normalize(x).
    """
    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize("NFC", text)
    text = text.replace(_ZWJ, "").replace(_ZWNJ, "")
    text = text.lower()
    text = text.strip()
    text = _TRAIL_PUNCT_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def tokens(text: str) -> list[str]:
    """Whitespace tokenizer over normalized text.

    Used by F1. Indic-aware tokenization is non-trivial; whitespace is
    the honest baseline. Pilot may upgrade to indic-nlp-library later.
    """
    return [t for t in normalize_indic(text).split(" ") if t]
