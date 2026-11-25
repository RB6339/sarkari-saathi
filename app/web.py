"""Web page for Sarkari Saathi (Gradio).

The handlers below are plain functions so they can be tested without a browser.
Each browser tab gets its own Session, kept in gr.State.
"""

from __future__ import annotations

import gradio as gr

from app.chat.session import Session

LANGUAGES = {"मराठी": "mr", "हिंदी": "hi", "English": "en"}

NO_KEY = {
    "mr": "सर्व्हरवर GROQ_API_KEY सेट केलेली नाही.",
    "hi": "सर्वर पर GROQ_API_KEY सेट नहीं है।",
    "en": "GROQ_API_KEY is not set on the server.",
}
VOICE_EMPTY = {
    "mr": "आवाज ऐकू आला नाही. पुन्हा बोला किंवा टाइप करा.",
    "hi": "आवाज़ सुनाई नहीं दी। फिर से बोलिए या टाइप कीजिए।",
    "en": "I couldn't hear anything. Please speak again or type.",
}
START_AGAIN = {"mr": "पुन्हा सुरू करा", "hi": "फिर से शुरू करें", "en": "Start again"}


def _default_client():
    from app.llm.client import GroqClient
    return GroqClient()


def to_markdown(text: str) -> str:
    """Keep the line breaks of result cards when shown as markdown."""
    return text.replace("\n", "  \n")


def start(lang_label: str, make_client=_default_client):
    lang = LANGUAGES.get(lang_label, "mr")
    try:
        session = Session(make_client(), lang=lang)
    except RuntimeError:
        return None, [{"role": "assistant", "content": NO_KEY[lang]}]
    return session, [{"role": "assistant", "content": session.start().text}]


def send(text: str, history: list, session):
    text = (text or "").strip()
    if not text or session is None:
        return "", history, session
    history = history + [{"role": "user", "content": text}]
    try:
        reply = session.handle(text)
        history.append({"role": "assistant", "content": to_markdown(reply.text)})
    except RuntimeError as err:
        history.append({"role": "assistant", "content": f"⚠️ {err}"})
    return "", history, session


def send_voice(audio_path: str | None, history: list, session):
    if not audio_path or session is None:
        return None, history, session
    try:
        text = session.client.transcribe(audio_path, language=session.lang)
    except RuntimeError as err:
        return None, history + [{"role": "assistant", "content": f"⚠️ {err}"}], session
    if not text:
        return None, history + [{"role": "assistant", "content": VOICE_EMPTY[session.lang]}], session
    _, history, session = send(text, history, session)
    return None, history, session


def build_ui(make_client=_default_client) -> gr.Blocks:
    with gr.Blocks(title="Sarkari Saathi") as demo:
        gr.Markdown(
            "# Sarkari Saathi\n"
            "सरकारी योजना शोधा · सरकारी योजनाएँ खोजें · Find government schemes you can get"
        )
        lang = gr.Radio(list(LANGUAGES), value="मराठी", label="भाषा / Language")
        chat = gr.Chatbot(height=480, label="Saathi")
        with gr.Row():
            box = gr.Textbox(placeholder="इथे लिहा... / यहाँ लिखें... / Type here...",
                             show_label=False, scale=5)
            send_btn = gr.Button("➤", scale=1, variant="primary")
        mic = gr.Audio(sources=["microphone"], type="filepath", label="🎤 बोला / बोलिए / Speak")
        restart = gr.Button(START_AGAIN["mr"])
        gr.Markdown(
            "<small>This is not an official government service. "
            "Always confirm on the official scheme website.</small>"
        )

        state = gr.State()

        def _start(label):
            session, history = start(label, make_client)
            return session, history, gr.update(value=START_AGAIN[LANGUAGES[label]])

        demo.load(_start, lang, [state, chat, restart])
        lang.change(_start, lang, [state, chat, restart])
        restart.click(_start, lang, [state, chat, restart])
        box.submit(send, [box, chat, state], [box, chat, state])
        send_btn.click(send, [box, chat, state], [box, chat, state])
        mic.stop_recording(send_voice, [mic, chat, state], [mic, chat, state])

    return demo
