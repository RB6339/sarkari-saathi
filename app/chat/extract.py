"""Pull profile answers out of what the user says.

The user can say a lot in one sentence, for example
"I'm a 45 year old farmer from Satara with 2 acres", which answers
age, state, owns_cultivable_land, is_cultivator and land size at once.

The LLM only reads the text and returns JSON. Everything it returns is
checked here: unknown fields are dropped and values must have the right type.
It never decides eligibility.

Try it:
    python -m app.chat.extract "मी साताऱ्याचा 45 वर्षांचा शेतकरी आहे, माझ्याकडे 2 एकर जमीन आहे"
"""

from __future__ import annotations

import json
import math
import sys

from app.eligibility.engine import load_fields

ACRES_PER_HECTARE = 2.471

SYSTEM_PROMPT = """You read what a person in India says about themselves and fill in a profile.
They may write in Marathi, Hindi, English or a mix.

Rules:
- Return a JSON object. Only include fields the person clearly stated or that follow directly
  from what they said. If you are not sure, leave the field out. Never guess.
- Use only the field names listed below.
- Booleans are true or false. Numbers are plain numbers (1 lakh = 100000).
- "state" is the Indian state name in English, e.g. "maharashtra". If they only name a
  district or city, use its state (e.g. Satara, Pune, Nashik -> maharashtra).
- "gender" is "male", "female" or "other".
- For land, if they give acres use "land_acres"; if they give hectares use "land_hectares".
- Saying they are a farmer who owns land means owns_cultivable_land = true and is_cultivator = true.

Fields:
{fields}
"""


def _field_list(fields: dict) -> str:
    lines = [f'- {name} ({spec["type"]}): {spec["question"]["en"]}' for name, spec in fields.items()]
    lines.append("- land_acres (float): How much farm land do you own, in acres?")
    return "\n".join(lines)


def _to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and v in (0, 1):
        return bool(v)
    if isinstance(v, str) and v.strip().lower() in {"true", "yes"}:
        return True
    if isinstance(v, str) and v.strip().lower() in {"false", "no"}:
        return False
    return None


def _to_number(v, kind):
    if isinstance(v, bool):
        return None
    try:
        if isinstance(v, str):
            v = v.replace(",", "").strip()
        n = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n) or n < 0:
        return None
    return int(n) if kind == "int" else n


def in_range(value, spec: dict) -> bool:
    """Reject impossible numbers like age 250."""
    lo, hi = spec.get("min"), spec.get("max")
    return (lo is None or value >= lo) and (hi is None or value <= hi)


def clean(raw: dict, fields: dict) -> dict:
    """Keep only known fields with valid values."""
    out = {}
    raw = dict(raw)

    acres = raw.pop("land_acres", None)
    if "land_hectares" not in raw and acres is not None:
        n = _to_number(acres, "float")
        if n is not None:
            raw["land_hectares"] = round(n / ACRES_PER_HECTARE, 2)

    for name, value in raw.items():
        spec = fields.get(name)
        if spec is None or value is None:
            continue
        kind = spec["type"]
        if kind == "bool":
            value = _to_bool(value)
        elif kind in ("int", "float"):
            value = _to_number(value, kind)
            if value is not None and not in_range(value, spec):
                value = None
        elif kind == "enum":
            value = str(value).strip().lower()
            value = spec.get("aliases", {}).get(value, value)
            if value not in spec["values"]:
                value = None
        else:
            value = str(value).strip().lower() or None
        if value is not None:
            out[name] = value
    return out


def extract_profile(text: str, client, fields: dict | None = None, asked_field: str | None = None) -> dict:
    """asked_field is the question we just asked, so a reply like "yes, two" has context."""
    fields = fields or load_fields()
    system = SYSTEM_PROMPT.format(fields=_field_list(fields))
    if asked_field:
        question = fields[asked_field]["question"]["en"]
        system += f'\nThe assistant just asked: "{question}" (field: {asked_field}).\n'
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    reply = client.chat(messages, json_mode=True)
    if not isinstance(reply, str):
        return {}
    try:
        raw = json.loads(reply)
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return clean(raw, fields)


if __name__ == "__main__":
    from app.llm.client import GroqClient

    sentence = " ".join(sys.argv[1:]) or "I am a 45 year old farmer from Satara with 2 acres of land"
    print(json.dumps(extract_profile(sentence, GroqClient()), ensure_ascii=False, indent=2))
