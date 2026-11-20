"""Quick CLI demo: answer questions, see which schemes you qualify for.

    python demo.py            # Marathi
    python demo.py en         # English
    python demo.py hi         # Hindi
"""

import sys

from app.chat.answers import parse_short_answer
from app.eligibility.engine import Status, evaluate_all, load_fields, load_schemes, next_question


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
        value = None
        while value is None:
            try:
                value = parse_short_answer(input(f"{spec['question'][lang]} > "), spec)
            except (EOFError, KeyboardInterrupt):
                print()
                return
        profile[field] = value

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
