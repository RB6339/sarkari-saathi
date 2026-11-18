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
