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
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


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

        try:
            resp = httpx.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
        except httpx.HTTPError as err:
            raise RuntimeError(f"Could not reach Groq ({type(err).__name__}). Check your internet connection.") from err

        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error {resp.status_code} for model '{self.model}': {resp.text[:300]}")
        try:
            return resp.json()["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError) as err:
            raise RuntimeError(f"Unexpected reply from Groq: {resp.text[:300]}") from err
