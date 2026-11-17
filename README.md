# Sarkari Saathi 🇮🇳

**A voice assistant that tells people — in Marathi, Hindi or English — which government schemes they qualify for, what documents they need, and how to apply.**

> Status: 🚧 Week 1 — 13 verified schemes + rule-based eligibility engine

## Why

Thousands of central and state schemes exist, but the people who need them most often don't know they qualify. Sarkari Saathi lets someone just *speak* in their own language and get a clear answer.

## Design principle: the LLM never decides eligibility

| Layer | Responsibility |
|---|---|
| **Rules engine** (`app/eligibility`) | Deterministic eligibility check from structured scheme rules. Three-valued logic: eligible / not eligible / need more info. |
| **LLM** (coming) | Conversation, language, extracting answers from free speech, explaining results. |
| **RAG** (coming) | Answers detailed questions from official scheme documents, with citations. |

This keeps answers auditable: every "you qualify" can be traced to a specific rule and an official source.

## Schemes covered (13)

| Scheme | Level | Category |
|---|---|---|
| PM-KISAN | Central | Agriculture |
| PM Fasal Bima Yojana | Central | Agriculture |
| PM Kisan Maandhan | Central | Pension |
| Atal Pension Yojana | Central | Pension |
| PM Jeevan Jyoti Bima | Central | Insurance |
| PM Suraksha Bima | Central | Insurance |
| PM Ujjwala Yojana | Central | Household |
| PM Matru Vandana Yojana | Central | Women & child |
| PM SVANidhi | Central | Livelihood |
| Namo Shetkari Mahasanman Nidhi | Maharashtra | Agriculture |
| Majhi Ladki Bahin Yojana | Maharashtra | Women |
| Shravanbal Seva Pension | Maharashtra | Pension |
| Gopinath Munde Shetkari Apghat Suraksha | Maharashtra | Insurance |

Every rule is checked against the scheme's page on [myScheme](https://www.myscheme.gov.in) (Government of India) and records `source_url` and `verified_on`. Conditions that can't be asked as a simple question (e.g. "first child only") are listed under `also_check` and shown to the user.

## Project structure

```
data/
  schemes/*.json        # one file per scheme: rules, benefit, documents, source
  profile_fields.json   # each user attribute + follow-up question in en/hi/mr
app/eligibility/engine.py
tests/
demo.py                 # CLI demo
```

## Scheme format

```json
{
  "id": "shravanbal",
  "states": ["maharashtra"],
  "eligibility": { "all_of": [
      {"field": "age", "op": "gte", "value": 65},
      {"any_of": [ {"field": "is_bpl", "op": "eq", "value": true},
                   {"field": "annual_family_income", "op": "lte", "value": 21000} ]}
  ] },
  "exclusions":  { "any_of": [] },
  "also_check": ["Applicant must be destitute"],
  "source_url": "https://www.myscheme.gov.in/schemes/...",
  "verified": true
}
```

Rules support nested `all_of` / `any_of` groups.

## Run

```bash
pip install -r requirements.txt
pytest
python demo.py      # Marathi  (en / hi also supported)
```

## Roadmap

- [x] Scheme data format + eligibility engine + tests
- [x] First 13 central + Maharashtra schemes
- [ ] 50–100 schemes
- [ ] LLM conversation layer (Marathi / Hindi / English)
- [ ] RAG over official scheme documents with citations
- [ ] Voice in / voice out
- [ ] Web app + deployment
- [ ] Evaluation set + accuracy report

## Disclaimer

Not an official government service. Always confirm on the official scheme website.
