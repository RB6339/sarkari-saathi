"""Edge cases found while testing. Each test is a bug that used to crash or give a wrong answer."""

import httpx
import pytest

from app.chat.answers import parse_short_answer
from app.chat.extract import clean, extract_profile
from app.chat.session import Session
from app.eligibility.engine import Status, evaluate, load_fields, load_schemes
from app.llm import client as client_module
from app.llm.client import GroqClient

FIELDS = load_fields()
SCHEMES = {s["id"]: s for s in load_schemes()}


class Reply:
    def __init__(self, value):
        self.value = value

    def chat(self, messages, json_mode=False, temperature=0.0):
        return self.value


# ---------- LLM / network problems must not crash the app ----------

def test_llm_returns_no_content():
    assert extract_profile("hello", Reply(None), FIELDS) == {}


@pytest.mark.parametrize("bad", ["NaN", "inf", "-inf", float("nan")])
def test_llm_returns_non_finite_number(bad):
    assert clean({"age": bad, "annual_family_income": bad}, FIELDS) == {}


def test_network_down_gives_clear_error(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("no internet")

    monkeypatch.setattr(client_module.httpx, "post", fail)
    with pytest.raises(RuntimeError, match="Could not reach Groq"):
        GroqClient(api_key="x").chat([])


def test_odd_200_reply_gives_clear_error(monkeypatch):
    monkeypatch.setattr(client_module.httpx, "post",
                        lambda *a, **k: httpx.Response(200, json={"error": "weird"}))
    with pytest.raises(RuntimeError, match="Unexpected reply"):
        GroqClient(api_key="x").chat([])


def test_null_content_becomes_empty_string(monkeypatch):
    monkeypatch.setattr(client_module.httpx, "post",
                        lambda *a, **k: httpx.Response(200, json={"choices": [{"message": {"content": None}}]}))
    assert GroqClient(api_key="x").chat([]) == ""


# ---------- impossible or unknown values are rejected ----------

def test_impossible_age_rejected():
    assert clean({"age": 250}, FIELDS) == {}
    assert parse_short_answer("999", FIELDS["age"]) is None
    assert parse_short_answer("70", FIELDS["age"]) == 70


def test_district_is_not_accepted_as_state():
    """A district like Satara used to be stored as the state, which made every
    Maharashtra scheme say 'not eligible'."""
    assert clean({"state": "Satara"}, FIELDS) == {}


def test_state_names_and_aliases():
    assert clean({"state": "Maharashtra"}, FIELDS) == {"state": "maharashtra"}
    assert clean({"state": "महाराष्ट्र"}, FIELDS) == {"state": "maharashtra"}
    assert parse_short_answer("महाराष्ट्र", FIELDS["state"]) == "maharashtra"
    assert parse_short_answer("Orissa", FIELDS["state"]) == "odisha"


def test_maharashtra_schemes_work_after_alias():
    p = {"state": clean({"state": "MH"}, FIELDS)["state"], "owns_cultivable_land": True,
         "is_pm_kisan_beneficiary": True}
    assert evaluate(SCHEMES["namo_shetkari"], p).status == Status.ELIGIBLE


def test_llm_bool_as_number():
    assert clean({"has_bank_account": 1, "is_bpl": 0}, FIELDS) == {"has_bank_account": True, "is_bpl": False}


# ---------- small things that annoyed users ----------

def test_no_pension_answered_with_no():
    assert parse_short_answer("nahi", FIELDS["monthly_pension"]) == 0
    assert parse_short_answer("नाही", FIELDS["monthly_pension"]) == 0
    assert parse_short_answer("nahi", FIELDS["age"]) is None   # "no" is not an age


def test_unclear_replies_do_not_loop_forever():
    s = Session(Reply("{}"), lang="en")
    first = s.handle("hello")
    second = s.handle("blah")
    third = s.handle("blah again")
    assert second.asked_field == first.asked_field      # asks once more
    assert third.asked_field != first.asked_field       # then moves on
    assert first.asked_field in s.skipped


def test_very_long_input_is_cut():
    seen = {}

    class Spy:
        def chat(self, messages, json_mode=False, temperature=0.0):
            seen["len"] = len(messages[-1]["content"])
            return "{}"

    Session(Spy(), lang="en").handle("a" * 50_000)
    assert seen["len"] <= Session.MAX_INPUT_CHARS
