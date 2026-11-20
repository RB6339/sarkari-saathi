import json

from app.chat.messages import results_message
from app.chat.session import Session
from app.eligibility.engine import load_schemes


class ScriptedClient:
    """Fake LLM that returns the next prepared reply each time it is called."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, json_mode=False, temperature=0.0):
        self.calls += 1
        return json.dumps(self.replies.pop(0) if self.replies else {})


FARMER = {"age": 45, "state": "maharashtra", "owns_cultivable_land": True,
          "is_cultivator": True, "land_acres": 2}

# What a 45-year-old male farmer with a bank account answers to every possible question.
FARMER_ANSWERS = {
    "gender": "पुरुष", "has_bank_account": "हो", "is_pm_kisan_beneficiary": "हो",
    "is_income_tax_payer": "नाही", "is_govt_employee": "नाही", "is_constitutional_post_holder": "नाही",
    "is_professional": "नाही", "monthly_pension": "0", "is_street_vendor": "नाही",
    "is_self_income_tax_payer": "नाही", "has_other_pension_scheme": "नाही",
    "household_has_lpg": "हो", "is_pregnant_or_new_mother": "नाही", "is_poor_household": "नाही",
    "is_bpl": "नाही", "annual_family_income": "120000", "owns_four_wheeler": "नाही",
}


def run(session, first_message, answers):
    reply = session.handle(first_message)
    turns = 1
    while not reply.done:
        reply = session.handle(answers[reply.asked_field])
        turns += 1
        assert turns < 40
    return reply, turns


def test_first_reply_is_a_question_in_marathi():
    s = Session(ScriptedClient([FARMER]), lang="mr")
    assert "नमस्कार" in s.start().text
    reply = s.handle("मी साताऱ्याचा 45 वर्षांचा शेतकरी आहे, 2 एकर जमीन आहे")
    assert not reply.done
    assert reply.asked_field not in {"age", "state", "owns_cultivable_land", "is_cultivator"}
    assert s.profile["land_hectares"] == 0.81


def test_full_farmer_conversation_uses_llm_once():
    client = ScriptedClient([FARMER])
    s = Session(client, lang="mr")
    reply, turns = run(s, "मी साताऱ्याचा 45 वर्षांचा शेतकरी आहे, 2 एकर जमीन आहे", FARMER_ANSWERS)
    assert client.calls == 1           # every later "हो"/"नाही" was parsed locally
    assert "पीएम-किसान सन्मान निधी" in reply.text
    assert "नमो शेतकरी" in reply.text
    assert "अटल पेन्शन" not in reply.text   # age 45 is over 40
    assert turns < 15


def test_unclear_reply_repeats_the_question():
    s = Session(ScriptedClient([FARMER, {}]), lang="en")
    first = s.handle("I am a 45 year old farmer from Satara with 2 acres")
    again = s.handle("hmm what do you mean")
    assert again.asked_field == first.asked_field
    assert again.text.startswith("Sorry")


def test_skipped_question_is_not_asked_again():
    s = Session(ScriptedClient([FARMER]), lang="mr")
    first = s.handle("मी साताऱ्याचा 45 वर्षांचा शेतकरी आहे, 2 एकर जमीन आहे")
    nxt = s.handle("माहित नाही")
    assert nxt.asked_field != first.asked_field
    assert first.asked_field in s.skipped


def test_llm_cannot_overwrite_earlier_answers():
    s = Session(ScriptedClient([{"age": 45}, {"age": 99, "has_bank_account": True}]), lang="en")
    s.handle("I am 45")
    s.handle("I have a bank account, and I am 99")
    assert s.profile["age"] == 45


def test_results_message_shows_data_exactly():
    scheme = {s["id"]: s for s in load_schemes()}["pm_kisan"]
    text = results_message([scheme], [], "hi")
    assert scheme["benefit"]["hi"] in text
    assert scheme["official_url"] in text
    assert "आधिकारिक" in text


def test_no_results_message():
    assert "सापडली नाही" in results_message([], [], "mr")


# The exact conversation from a real run: 35-year-old pregnant street vendor, no bank account, no land.
VENDOR_ANSWERS = {
    "has_bank_account": "nahi", "owns_cultivable_land": "nahi", "gender": "mahila",
    "is_poor_household": "ho", "state": "maharashtra", "is_street_vendor": "ho",
    "household_has_lpg": "nahi", "is_cultivator": "nahi", "is_pregnant_or_new_mother": "ho",
    "is_govt_employee": "nahi", "is_pm_kisan_beneficiary": "nahi",
}


def test_vendor_is_not_asked_about_pm_kisan_and_gets_bank_tip():
    s = Session(ScriptedClient([{"age": 35}]), lang="mr")
    reply = s.handle("35")
    asked = []
    while not reply.done:
        asked.append(reply.asked_field)
        reply = s.handle(VENDOR_ANSWERS[reply.asked_field])
    assert "is_pm_kisan_beneficiary" not in asked
    assert "पीएम स्वनिधी" in reply.text
    assert "जन धन" in reply.text
    assert "माझी लाडकी बहीण" in reply.text
