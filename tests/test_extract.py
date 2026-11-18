import json

from app.chat.extract import clean, extract_profile
from app.eligibility.engine import load_fields

FIELDS = load_fields()


class FakeClient:
    """Stands in for the LLM so tests run without a key or network."""

    def __init__(self, reply):
        self.reply = reply
        self.messages = None

    def chat(self, messages, json_mode=False, temperature=0.0):
        self.messages = messages
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def test_farmer_sentence():
    client = FakeClient({"age": 45, "state": "Maharashtra", "owns_cultivable_land": True,
                         "is_cultivator": True, "land_acres": 2})
    p = extract_profile("I am a 45 year old farmer from Satara with 2 acres", client, FIELDS)
    assert p == {"age": 45, "state": "maharashtra", "owns_cultivable_land": True,
                 "is_cultivator": True, "land_hectares": 0.81}


def test_unknown_fields_are_dropped():
    assert clean({"favourite_colour": "blue", "age": 30}, FIELDS) == {"age": 30}


def test_bad_values_are_dropped():
    p = clean({"age": "old", "gender": "robot", "has_bank_account": "maybe",
               "annual_family_income": -5}, FIELDS)
    assert p == {}


def test_values_are_converted():
    p = clean({"age": "30", "annual_family_income": "2,50,000", "has_bank_account": "yes",
               "gender": "Female"}, FIELDS)
    assert p == {"age": 30, "annual_family_income": 250000, "has_bank_account": True, "gender": "female"}


def test_hectares_win_over_acres():
    assert clean({"land_hectares": 1.0, "land_acres": 5}, FIELDS) == {"land_hectares": 1.0}


def test_bad_json_from_llm_returns_empty():
    assert extract_profile("hello", FakeClient("not json"), FIELDS) == {}
    assert extract_profile("hello", FakeClient("[1, 2]"), FIELDS) == {}


def test_prompt_lists_every_field():
    client = FakeClient({})
    extract_profile("hello", client, FIELDS)
    system = client.messages[0]["content"]
    for name in FIELDS:
        assert name in system
