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
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
SPEECH_MODEL = os.getenv("GROQ_SPEECH_MODEL", "whisper-large-v3")

# A short example sentence in the user's language. Whisper uses it as a hint for
# spelling and vocabulary, which helps a lot with Marathi words like "एकर" or "शेतकरी".
SPEECH_HINTS = {
    "mr": "नमस्कार. मी शेतकरी आहे. माझं वय 45 वर्षे आहे. मी सातारा, महाराष्ट्र येथे राहतो. "
          "माझ्याकडे 2 एकर जमीन आहे. माझं बँक खातं आहे. हो. नाही. माहित नाही.",
    "hi": "नमस्ते. मैं किसान हूँ. मेरी उम्र 45 साल है. मैं पुणे, महाराष्ट्र में रहता हूँ. "
          "मेरे पास 2 एकड़ ज़मीन है. मेरा बैंक खाता है. हाँ. नहीं. पता नहीं.",
}


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

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        """Speech to text with Whisper. language is "mr", "hi" or "en" (helps accuracy)."""
        data = {"model": SPEECH_MODEL, "response_format": "json", "temperature": "0"}
        if language:
            data["language"] = language
        if language in SPEECH_HINTS:
            data["prompt"] = SPEECH_HINTS[language]
        try:
            with open(audio_path, "rb") as f:
                resp = httpx.post(
                    GROQ_AUDIO_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                    files={"file": (os.path.basename(audio_path), f)},
                    timeout=60.0,
                )
        except httpx.HTTPError as err:
            raise RuntimeError(f"Could not reach Groq ({type(err).__name__}). Check your internet connection.") from err

        if resp.status_code != 200:
            raise RuntimeError(f"Groq speech error {resp.status_code}: {resp.text[:300]}")
        try:
            return (resp.json().get("text") or "").strip()
        except ValueError as err:
            raise RuntimeError(f"Unexpected reply from Groq: {resp.text[:300]}") from err
