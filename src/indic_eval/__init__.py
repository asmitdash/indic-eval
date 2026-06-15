"""indic-eval — eval harness, observability SDK, and public leaderboard for Indic LLMs."""
from __future__ import annotations
import os
from pathlib import Path

__version__ = "0.1.0"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        cand = parent / ".env"
        if cand.is_file():
            load_dotenv(cand, override=False)
            return


_load_dotenv()
