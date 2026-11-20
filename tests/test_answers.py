from app.chat.answers import is_skip, parse_short_answer

BOOL = {"type": "bool"}
INT = {"type": "int"}
FLOAT = {"type": "float"}
GENDER = {"type": "enum", "values": ["male", "female", "other"]}


def test_yes_no_in_three_languages():
    for word in ["yes", "हो", "होय", "हाँ", "Haan"]:
        assert parse_short_answer(word, BOOL) is True
    for word in ["no", "नाही", "नहीं", "nahi"]:
        assert parse_short_answer(word, BOOL) is False


def test_numbers():
    assert parse_short_answer("45", INT) == 45
    assert parse_short_answer("४५", INT) == 45
    assert parse_short_answer("2,50,000", INT) == 250000
    assert parse_short_answer("2 लाख", INT) == 200000
    assert parse_short_answer("1.5", FLOAT) == 1.5


def test_gender():
    assert parse_short_answer("महिला", GENDER) == "female"
    assert parse_short_answer("पुरुष", GENDER) == "male"


def test_longer_replies_are_left_for_the_llm():
    assert parse_short_answer("yes I have a ration card and a bank account", BOOL) is None
    assert parse_short_answer("I am 45 years old", INT) is None


def test_skip():
    assert is_skip("माहित नाही")
    assert is_skip("Don't know")
    assert not is_skip("नाही")
