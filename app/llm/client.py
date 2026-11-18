"""Small wrapper around the Groq chat API.

Groq's API follows the OpenAI chat format, so this is just one POST request.
The key is read from the GROQ_API_KEY environment variable (put it in .env).
"""

from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict], json_mode: bool = False, temperature: float = 0.0) -> str:
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
