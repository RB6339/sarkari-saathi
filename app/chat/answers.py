"""Understand short replies to a question without calling the LLM.

Most replies to a question are one word: "हो", "नाही", "45", "महिला".
We can read those ourselves, which is faster, free and can't go wrong
the way an LLM can. Anything longer goes to the LLM.
"""

from __future__ import annotations

import re

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

YES = {"yes", "y", "yeah", "haan", "ha", "ho", "hoy", "हाँ", "हां", "हा", "जी", "हो", "होय", "true"}
NO = {"no", "n", "nahi", "nahin", "nai", "नहीं", "नही", "ना", "नाही", "नको", "false"}
SKIP = {"skip", "dont know", "don't know", "not sure", "pata nahi", "पता नहीं", "मालूम नहीं",
        "माहित नाही", "माहीत नाही", "सांगता येणार नाही"}

GENDER = {
    "male": {"male", "man", "m", "purush", "पुरुष", "आदमी", "मर्द"},
    "female": {"female", "woman", "f", "mahila", "महिला", "स्त्री", "औरत", "बाई"},
    "other": {"other", "अन्य", "इतर"},
}


def _norm(text: str) -> str:
    text = text.strip().lower().translate(DEVANAGARI_DIGITS)
    return re.sub(r"[.!?,।]+$", "", text).strip()


def is_skip(text: str) -> bool:
    return _norm(text) in SKIP


def parse_short_answer(text: str, spec: dict):
    """Return the value for one field, or None if the reply isn't a simple answer."""
    value = _parse(_norm(text), spec)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        lo, hi = spec.get("min"), spec.get("max")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            return None
    return value


def _parse(t: str, spec: dict):
    kind = spec["type"]

    if kind == "bool":
        if t in YES:
            return True
        if t in NO:
            return False
        return None

    if kind in ("int", "float"):
        if t in NO and spec.get("none_is_zero"):
            return 0
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:lakh|लाख)?", t.replace(",", ""))
        if not m:
            return None
        n = float(m.group(1))
        if "lakh" in t or "लाख" in t:
            n *= 100000
        return int(n) if kind == "int" else n

    if kind == "enum":
        values = spec.get("values", [])
        t = spec.get("aliases", {}).get(t, t)
        if t in values:
            return t
        for value, words in GENDER.items():
            if t in words and value in values:
                return value
        return None

    return None
