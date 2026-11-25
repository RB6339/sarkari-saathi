import json

from app.web import build_ui, send, send_voice, start, to_markdown


class FakeClient:
    def __init__(self, extract=None, heard="35"):
        self.extract = extract or {"age": 35}
        self.heard = heard
        self.transcribed = []

    def chat(self, messages, json_mode=False, temperature=0.0):
        return json.dumps(self.extract)

    def transcribe(self, path, language=None):
        self.transcribed.append(language)
        return self.heard


def test_start_in_each_language():
    for label, word in [("मराठी", "नमस्कार"), ("हिंदी", "नमस्ते"), ("English", "Hello")]:
        session, history = start(label, FakeClient)
        assert word in history[0]["content"]


def test_start_without_key_shows_message():
    def no_key():
        raise RuntimeError("GROQ_API_KEY is not set")

    session, history = start("English", no_key)
    assert session is None
    assert "GROQ_API_KEY" in history[0]["content"]


def test_send_adds_user_and_bot_messages():
    session, history = start("English", FakeClient)
    box, history, session = send("I am 35", history, session)
    assert box == ""
    assert history[-2] == {"role": "user", "content": "I am 35"}
    assert history[-1]["role"] == "assistant"
    assert session.profile["age"] == 35


def test_empty_message_does_nothing():
    session, history = start("English", FakeClient)
    _, after, _ = send("   ", history, session)
    assert after == history


def test_voice_uses_session_language():
    client = FakeClient()
    session, history = start("मराठी", lambda: client)
    _, history, session = send_voice("/tmp/voice.webm", history, session)
    assert client.transcribed == ["mr"]
    assert history[-2]["content"] == "🎤 35"   # user sees exactly what was heard


def test_silent_recording():
    session, history = start("हिंदी", lambda: FakeClient(heard=""))
    _, history, _ = send_voice("/tmp/voice.webm", history, session)
    assert "आवाज़" in history[-1]["content"]


def test_api_error_is_shown_not_raised():
    class Broken(FakeClient):
        def chat(self, *a, **k):
            raise RuntimeError("Could not reach Groq")

    session, history = start("English", Broken)
    _, history, _ = send("I am a farmer", history, session)
    assert "Could not reach Groq" in history[-1]["content"]


def test_markdown_keeps_line_breaks():
    assert to_markdown("a\nb") == "a  \nb"


def test_ui_builds():
    assert build_ui(FakeClient) is not None


def test_chatbot_uses_role_content_messages():
    """Gradio 5 defaults to an old 'tuples' format, which breaks our role/content messages."""
    import gradio as gr

    demo = build_ui(FakeClient)
    chatbots = [b for b in demo.blocks.values() if isinstance(b, gr.Chatbot)]
    assert chatbots and getattr(chatbots[0], "type", "messages") == "messages"
