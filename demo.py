"""Quick CLI demo: answer questions, see which schemes you qualify for.

    python demo.py            # Marathi
    python demo.py en         # English
    python demo.py hi         # Hindi
"""

import sys

from app.eligibility.engine import Status, evaluate_all, load_fields, load_schemes, next_question

YES = {"y", "yes", "ho", "हो", "हाँ", "हां", "ha", "haan", "true", "1"}


def parse(raw: str, ftype: str):
    raw = raw.strip()
    if ftype == "int":
        return int(raw.replace(",", ""))
    if ftype == "float":
        return float(raw)
    if ftype == "bool":
        return raw.lower() in YES
    return raw.lower()


def main(lang: str = "mr") -> None:
    schemes, fields = load_schemes(), load_fields()
    names = {s["id"]: s for s in schemes}
    profile: dict = {}

    while True:
        results = evaluate_all(schemes, profile)
        field = next_question(results)
        if field is None:
            break
        spec = fields[field]
        profile[field] = parse(input(f"{spec['question'][lang]} > "), spec["type"])

    print()
    for r in results:
        s = names[r.scheme_id]
        mark = "✅" if r.status == Status.ELIGIBLE else "❌"
        print(f"{mark} {s['name'][lang]}")
        if r.status == Status.ELIGIBLE:
            print(f"   {s['benefit'][lang]}")
            print(f"   {s['how_to_apply'][lang]}")
            for note in s.get("also_check", []):
                print(f"   ⚠️  {note}")
            print(f"   🔗 {s['official_url']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mr")
