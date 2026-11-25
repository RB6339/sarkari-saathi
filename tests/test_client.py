import httpx
import pytest

from app.llm import client as client_module
from app.llm.client import GroqClient


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        GroqClient()


def test_api_error_shows_model_and_reason(monkeypatch):
    def fake_post(url, **kwargs):
        return httpx.Response(404, json={"error": {"message": "model not found"}})

    monkeypatch.setattr(client_module.httpx, "post", fake_post)
    c = GroqClient(api_key="test", model="old-model")
    with pytest.raises(RuntimeError, match="404.*old-model.*model not found"):
        c.chat([{"role": "user", "content": "hi"}])


def test_returns_message_text(monkeypatch):
    def fake_post(url, **kwargs):
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})

    monkeypatch.setattr(client_module.httpx, "post", fake_post)
    assert GroqClient(api_key="test").chat([{"role": "user", "content": "hi"}]) == "hello"


def test_transcribe_sends_language_and_returns_text(monkeypatch, tmp_path):
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["data"] = kwargs["data"]
        return httpx.Response(200, json={"text": "  मी शेतकरी आहे  "})

    audio = tmp_path / "voice.webm"
    audio.write_bytes(b"fake audio")
    monkeypatch.setattr(client_module.httpx, "post", fake_post)
    text = GroqClient(api_key="test").transcribe(str(audio), language="mr")
    assert text == "मी शेतकरी आहे"
    assert seen["url"].endswith("/audio/transcriptions")
    assert seen["data"]["language"] == "mr"


def test_transcribe_error(monkeypatch, tmp_path):
    audio = tmp_path / "voice.webm"
    audio.write_bytes(b"x")
    monkeypatch.setattr(client_module.httpx, "post", lambda *a, **k: httpx.Response(400, text="bad audio"))
    with pytest.raises(RuntimeError, match="speech error 400"):
        GroqClient(api_key="test").transcribe(str(audio))
