"""Chat with Sarkari Saathi in the terminal.

    python chat.py          # Marathi
    python chat.py hi       # Hindi
    python chat.py en       # English

Type "exit" to stop. Needs GROQ_API_KEY in .env.
"""

import sys

from app.chat.session import Session
from app.llm.client import GroqClient

EXIT_WORDS = {"exit", "quit", "bye", "बस", "थांबा"}


def main(lang: str = "mr") -> None:
    if lang not in {"mr", "hi", "en"}:
        sys.exit("Language must be mr, hi or en")

    session = Session(GroqClient(), lang=lang)
    print(f"\nSaathi: {session.start().text}\n")

    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in EXIT_WORDS:
            break
        if not text:
            continue

        try:
            reply = session.handle(text)
        except RuntimeError as err:
            print(f"\n[error] {err}\n")
            continue

        print(f"\nSaathi: {reply.text}\n")
        if reply.done:
            break


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mr")
