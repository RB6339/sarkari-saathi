# Sarkari Saathi

An assistant that helps people find which government schemes they can get, in Marathi, Hindi or English. You answer a few simple questions and it tells you which schemes you qualify for, what documents you need and how to apply.

Right now this repo has the eligibility engine and the scheme data. The chat and voice parts are next.

## Why I built this

There are hundreds of central and state schemes, and most people who need them don't know they qualify. The official portals are long forms in English. I wanted something you can just talk to in your own language.

## How it works

The eligibility decision is made by plain rules, not by an LLM. LLMs can make mistakes with things like age limits or income limits, so I keep each scheme's rules as JSON and check them in code. The LLM (coming next) will only handle the conversation and explain the result.

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
data/schemes/               one JSON file per scheme
data/profile_fields.json    questions in English, Hindi and Marathi
tests/                      pytest tests
demo.py                     small command line demo
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
python demo.py        # Marathi
python demo.py en     # English
python demo.py hi     # Hindi
```

## To do

- [x] Rules engine and tests
- [x] First 13 schemes
- [ ] More schemes (target 50+)
- [ ] Chat layer with an LLM
- [ ] Answer questions from official scheme documents
- [ ] Voice input and output
- [ ] Web app
- [ ] Accuracy test set

## Note

This is not an official government app. Please confirm details on the official scheme website before applying.
