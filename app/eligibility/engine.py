"""Rule-based eligibility engine.

The LLM never decides eligibility. Scheme rules are stored as structured JSON
and evaluated here with three-valued logic:

    True   -> condition satisfied
    False  -> condition not satisfied
    None   -> we don't know yet (field missing from the user's profile)

Unknown fields are reported back so the chat layer can ask the user for them.

Rule nodes:
    {"field": "age", "op": "gte", "value": 18}      # leaf condition
    {"any_of": [node, node, ...]}                    # OR group
    {"all_of": [node, node, ...]}                    # AND group
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

_OPS = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "in": lambda a, b: a in b,
}


class Status(str, Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    NEED_INFO = "need_info"


@dataclass
class Result:
    scheme_id: str
    status: Status
    missing_fields: list[str] = field(default_factory=list)
    failed_conditions: list[dict] = field(default_factory=list)
    matched_exclusions: list[dict] = field(default_factory=list)


def _normalise(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


def _eval(node: dict, profile: dict) -> tuple[bool | None, list[str]]:
    """Evaluate a rule node. Returns (value, missing_fields)."""
    if "any_of" in node:
        missing: list[str] = []
        unknown = False
        for child in node["any_of"]:
            val, miss = _eval(child, profile)
            if val is True:
                return True, []
            if val is None:
                unknown = True
                missing += miss
        return (None, missing) if unknown else (False, [])

    if "all_of" in node:
        missing = []
        unknown = False
        for child in node["all_of"]:
            val, miss = _eval(child, profile)
            if val is False:
                return False, []
            if val is None:
                unknown = True
                missing += miss
        return (None, missing) if unknown else (True, [])

    value = profile.get(node["field"])
    if value is None:
        return None, [node["field"]]
    return bool(_OPS[node["op"]](_normalise(value), _normalise(node["value"]))), []


def evaluate(scheme: dict, profile: dict) -> Result:
    sid = scheme["id"]
    missing: list[str] = []

    # 1. State applicability
    states = [s.lower() for s in scheme.get("states", ["*"])]
    if "*" not in states:
        user_state = _normalise(profile.get("state"))
        if user_state is None:
            missing.append("state")
        elif user_state not in states:
            return Result(sid, Status.NOT_ELIGIBLE,
                          failed_conditions=[{"field": "state", "op": "in", "value": states}])

    # 2. Positive conditions (every top-level node must hold)
    failed = []
    for node in scheme.get("eligibility", {}).get("all_of", []):
        val, miss = _eval(node, profile)
        if val is None:
            missing += miss
        elif not val:
            failed.append(node)
    if failed:
        return Result(sid, Status.NOT_ELIGIBLE, failed_conditions=failed)

    # 3. Exclusions (any one disqualifies)
    hits = []
    for node in scheme.get("exclusions", {}).get("any_of", []):
        val, miss = _eval(node, profile)
        if val is None:
            missing += miss
        elif val:
            hits.append(node)
    if hits:
        return Result(sid, Status.NOT_ELIGIBLE, matched_exclusions=hits)

    if missing:
        return Result(sid, Status.NEED_INFO, missing_fields=list(dict.fromkeys(missing)))
    return Result(sid, Status.ELIGIBLE)


def load_schemes(directory: Path = DATA_DIR / "schemes") -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]


def load_fields(path: Path = DATA_DIR / "profile_fields.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_all(schemes: list[dict], profile: dict) -> list[Result]:
    return [evaluate(s, profile) for s in schemes]


def next_question(results: list[Result]) -> str | None:
    """Pick the missing field that unblocks the most schemes."""
    counts = Counter(f for r in results if r.status == Status.NEED_INFO for f in r.missing_fields)
    return counts.most_common(1)[0][0] if counts else None
