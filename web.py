"""Run the Sarkari Saathi web page.

    python web.py

Then open http://127.0.0.1:7860 in your browser. Needs GROQ_API_KEY in .env.
"""

from app.web import build_ui

if __name__ == "__main__":
    build_ui().launch()
