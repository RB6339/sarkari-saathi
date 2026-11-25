# Sarkari Saathi

An assistant that helps people find which government schemes they can get, in Marathi, Hindi or English. You answer a few simple questions and it tells you which schemes you qualify for, what documents you need and how to apply.

You can use it as a web page (type or speak) or in the terminal.

## Why I built this

There are hundreds of central and state schemes, and most people who need them don't know they qualify. The official portals are long forms in English. I wanted something you can just talk to in your own language.

## How it works

The eligibility decision is made by plain rules, not by an LLM. LLMs can make mistakes with things like age limits or income limits, so I keep each scheme's rules as JSON and check them in code. The LLM only reads what the user says and turns it into answers like age, state or land size. Short replies like "हो", "नाही" or "45" are read by simple code without calling the LLM at all.

Each scheme gets one of three results:

- eligible: all rules pass
- not eligible: at least one rule fails
- need info: nothing has failed yet but some answers are missing

When answers are missing, the engine asks the question that is missing from the most schemes, so the user answers as few questions as possible.

## Schemes

13 schemes so far, 9 central and 4 Maharashtra:

| Scheme | Level | Type |
|---|---|---|
| PM-KISAN | Central | Agriculture |
| PM Fasal Bima Yojana | Central | Agriculture |
| PM Kisan Maandhan | Central | Pension |
| Atal Pension Yojana | Central | Pension |
| PM Jeevan Jyoti Bima | Central | Insurance |
| PM Suraksha Bima | Central | Insurance |
| PM Ujjwala Yojana | Central | Household |
| PM Matru Vandana Yojana | Central | Women and child |
| PM SVANidhi | Central | Livelihood |
| Namo Shetkari Mahasanman Nidhi | Maharashtra | Agriculture |
| Majhi Ladki Bahin Yojana | Maharashtra | Women |
| Shravanbal Seva Pension | Maharashtra | Pension |
| Gopinath Munde Shetkari Apghat Suraksha | Maharashtra | Insurance |

I took the rules from each scheme's page on [myScheme](https://www.myscheme.gov.in). Every scheme file has a `source_url` and the date I checked it. Some conditions are hard to ask as a yes/no question (for example "first child only"), so those are kept in `also_check` and shown to the user as a note.

## Folder structure

```
app/eligibility/engine.py   rules engine
app/chat/extract.py         LLM reads free text into profile answers
app/chat/answers.py         reads short replies (yes/no/numbers) without the LLM
app/chat/session.py         one conversation: read reply, check rules, ask next question
app/chat/messages.py        fixed text and result cards in en/hi/mr
app/llm/client.py           Groq API client (chat and speech-to-text)
app/web.py                  web page (Gradio)
data/schemes/               one JSON file per scheme
data/profile_fields.json    questions in English, Hindi and Marathi
tests/                      pytest tests
web.py                      starts the web page
chat.py                     terminal chat
demo.py                     question-by-question demo without the LLM
```

## Scheme file example

```json
{
  "id": "shravanbal",
  "states": ["maharashtra"],
  "eligibility": { "all_of": [
      {"field": "age", "op": "gte", "value": 65},
      {"any_of": [ {"field": "is_bpl", "op": "eq", "value": true},
                   {"field": "annual_family_income", "op": "lte", "value": 21000} ]}
  ] },
  "exclusions": { "any_of": [] },
  "also_check": ["Applicant must be destitute"],
  "source_url": "https://www.myscheme.gov.in/schemes/sbssps",
  "verified": true
}
```

`all_of` means every rule must pass, `any_of` means at least one must pass. They can be nested.

## Running it

```bash
pip install -r requirements.txt
pytest
```

For the chat you need a free API key from [Groq](https://console.groq.com). Make a file called `.env`:

```
GROQ_API_KEY=your_key_here
```

Web page (type or press the mic and speak):

```bash
python web.py
```

and open http://127.0.0.1:7860. Speech is turned into text with Whisper on Groq.

Terminal:

```bash
python chat.py        # Marathi
python chat.py hi     # Hindi
python chat.py en     # English
```

Example:

```
Saathi: नमस्कार! तुमच्याबद्दल थोडं सांगा: तुमचं वय, तुम्ही कुठे राहता आणि काय काम करता.
You: मी साताऱ्याचा 45 वर्षांचा शेतकरी आहे, 2 एकर जमीन आहे
Saathi: तुम्ही पुरुष आहात की महिला?
You: पुरुष
...
Saathi: तुम्ही या योजनांसाठी पात्र असू शकता:
* पीएम-किसान सन्मान निधी
  लाभ: प्रति कुटुंब दरवर्षी ₹6,000, ₹2,000 च्या 3 हप्त्यांत थेट बँक खात्यात
...
```

`demo.py` asks every question one by one and doesn't need a key.

## To do

- [x] Rules engine and tests
- [x] First 13 schemes
- [ ] More schemes (target 50+)
- [x] Chat in the terminal with an LLM
- [ ] Translate documents and notes into Hindi and Marathi
- [ ] Answer questions from official scheme documents
- [x] Voice input
- [ ] Voice output (read the answer aloud)
- [x] Web app
- [ ] Put it online on Hugging Face Spaces
- [ ] Accuracy test set

## Note

This is not an official government app. Please confirm details on the official scheme website before applying.
