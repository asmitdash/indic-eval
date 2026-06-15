"""Scoring metrics. Pure functions over (model output, reference, metadata).

Designed so that benchmarks can compose metrics:
  - exact_match — strictest
  - contains — looser, tolerates lead-in chatter
  - transliteration_round_trip — robustness probe (Roman <-> Devanagari)
  - script_purity — fraction of characters in the expected script
  - code_mix_index — Hinglish quality signal (Devanagari token ratio)
  - semantic_judge_score — LLM judge fallback for free-form generation
"""
from __future__ import annotations
import re
import unicodedata
from typing import Optional


# -- Unicode block helpers --------------------------------------------------

# Block ranges from the Unicode standard. We keep them tight (only used scripts).
_BLOCKS: dict[str, tuple[int, int]] = {
    "latin": (0x0000, 0x024F),
    "devanagari": (0x0900, 0x097F),
    "bengali": (0x0980, 0x09FF),
    "gurmukhi": (0x0A00, 0x0A7F),
    "gujarati": (0x0A80, 0x0AFF),
    "odia": (0x0B00, 0x0B7F),
    "tamil": (0x0B80, 0x0BFF),
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
    "malayalam": (0x0D00, 0x0D7F),
}


def _in_block(ch: str, block: str) -> bool:
    lo, hi = _BLOCKS[block]
    return lo <= ord(ch) <= hi


# -- Metrics ----------------------------------------------------------------

def _norm(s: str) -> str:
    """NFKC + lowercase + collapse whitespace. Stable comparison."""
    s = unicodedata.normalize("NFKC", s).strip().lower()
    return " ".join(s.split())


def exact_match(output: str, reference: str) -> float:
    return 1.0 if _norm(output) == _norm(reference) else 0.0


def contains(output: str, reference: str) -> float:
    return 1.0 if _norm(reference) in _norm(output) else 0.0


def script_purity(text: str, expected_script: str) -> float:
    """Fraction of letter characters that belong to the expected script.

    Treats whitespace, digits, and ASCII punctuation as neutral.
    A model writing Hindi answers in Latin script will score ~0.0.
    """
    if expected_script not in _BLOCKS:
        raise ValueError(f"Unknown script: {expected_script}")
    letter_chars = [c for c in text if c.isalpha()]
    if not letter_chars:
        return 0.0
    in_block = sum(1 for c in letter_chars if _in_block(c, expected_script))
    return in_block / len(letter_chars)


def code_mix_index(text: str) -> float:
    """Devanagari fraction among letter characters.

    For Hinglish-flavoured prompts, models that go full-English (0.0) or
    full-Hindi (1.0) both lose; the codemix sweet spot is ~0.3-0.7. This is
    informational — a benchmark may either reward proximity to a target
    fraction or raw fraction depending on the test.
    """
    letter_chars = [c for c in text if c.isalpha()]
    if not letter_chars:
        return 0.0
    deva = sum(1 for c in letter_chars if _in_block(c, "devanagari"))
    return deva / len(letter_chars)


def transliteration_round_trip(output: str, reference_devanagari: str,
                                reference_latin: Optional[str] = None) -> float:
    """Score robustness to script-mixing.

    The benchmark provides a phrase in Devanagari + (optionally) its standard
    Latin transliteration. We accept either form (or a sufficiently close
    contains-match) — penalising only models that produce neither.
    """
    if contains(output, reference_devanagari) >= 1.0:
        return 1.0
    if reference_latin and contains(output, reference_latin) >= 1.0:
        return 1.0
    # partial credit for any Devanagari presence
    if any(_in_block(c, "devanagari") for c in output):
        return 0.5
    return 0.0


# Lazy import for the judge so the rest of the module is dependency-free.
def semantic_judge_score(output: str, reference: str, *, judge_client=None,
                          model_id: Optional[str] = None) -> float:
    """LLM-judge score on a 0.0-1.0 scale for free-form generation.

    Uses Claude Opus 4.7 on Bedrock by default (per Asmit's CLAUDE.md). The
    rubric is intentionally narrow: faithfulness to the reference's intent,
    not "helpfulness." Returns 0.0 on judge failure rather than raising — eval
    runs over thousands of examples must not blow up on a single bad call.
    """
    import os
    if judge_client is None:
        try:
            from anthropic import AnthropicBedrock
            judge_client = AnthropicBedrock(aws_region=os.getenv("BEDROCK_REGION", "ap-south-1"))
        except Exception:
            return 0.0
    model_id = model_id or os.getenv("INDIC_EVAL_JUDGE_MODEL", "global.anthropic.claude-opus-4-7")

    prompt = (
        "You are a careful evaluator for a non-English LLM benchmark. Given a "
        "REFERENCE answer and a CANDIDATE answer, output a single float in "
        "[0.0, 1.0] reflecting how faithfully the candidate captures the meaning "
        "of the reference. Only the float, nothing else. 0.0 = wrong / unrelated; "
        "0.5 = partially correct but missing key facts; 1.0 = fully correct.\n\n"
        f"REFERENCE: {reference}\n\nCANDIDATE: {output}\n\nSCORE:"
    )
    try:
        resp = judge_client.messages.create(
            model=model_id, max_tokens=8,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        m = re.search(r"\d+\.?\d*", text)
        if not m:
            return 0.0
        return max(0.0, min(1.0, float(m.group(0))))
    except Exception:
        return 0.0
