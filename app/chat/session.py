"""One conversation with one user.

Each turn:
1. Read the user's reply. Short replies ("हो", "45") are parsed locally;
   longer ones go to the LLM to pull out profile answers.
2. Run the rules engine on everything we know so far.
3. If answers are still missing, ask the most useful next question.
   Otherwise show the results.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.chat.answers import is_skip, parse_short_answer
from app.chat.extract import extract_profile
from app.chat.messages import results_message, t
from app.eligibility.engine import Status, evaluate_all, load_fields, load_schemes


@dataclass
class Reply:
    text: str
    done: bool = False
    asked_field: str | None = None


@dataclass
class Session:
    client: object
    lang: str = "mr"
    schemes: list[dict] = field(default_factory=load_schemes)
    fields: dict = field(default_factory=load_fields)
    profile: dict = field(default_factory=dict)
    skipped: set[str] = field(default_factory=set)
    asked_field: str | None = None
    llm_calls: int = 0

    def start(self) -> Reply:
        return Reply(t("welcome", self.lang))

    def handle(self, text: str) -> Reply:
        text = text.strip()
        understood = self._read(text) if text else False

        results = evaluate_all(self.schemes, self.profile)
        field_name = self._next_field(results)

        if field_name is None:
            self.asked_field = None
            return Reply(self._results_text(results), done=True)

        question = self.fields[field_name]["question"][self.lang]
        if not understood and field_name == self.asked_field:
            question = f"{t('not_understood', self.lang)} {question}"
        self.asked_field = field_name
        return Reply(question, asked_field=field_name)

    def _read(self, text: str) -> bool:
        """Update the profile from the user's reply. Returns True if we learned something."""
        asked = self.asked_field
        if asked:
            if is_skip(text):
                self.skipped.add(asked)
                return True
            value = parse_short_answer(text, self.fields[asked])
            if value is not None:
                self.profile[asked] = value
                return True

        self.llm_calls += 1
        found = extract_profile(text, self.client, self.fields, asked_field=asked)
        found = {k: v for k, v in found.items() if k not in self.profile or k == asked}
        self.profile.update(found)
        return bool(found)

    def _next_field(self, results) -> str | None:
        counts = Counter(
            f for r in results if r.status == Status.NEED_INFO
            for f in r.missing_fields if f not in self.skipped
        )
        return counts.most_common(1)[0][0] if counts else None

    def _results_text(self, results) -> str:
        by_id = {s["id"]: s for s in self.schemes}
        eligible = [by_id[r.scheme_id] for r in results if r.status == Status.ELIGIBLE]
        maybe = [by_id[r.scheme_id] for r in results if r.status == Status.NEED_INFO]
        return results_message(eligible, maybe, self.lang)
