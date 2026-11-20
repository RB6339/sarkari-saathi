"""Fixed text shown to the user, in English, Hindi and Marathi.

Results are written from the scheme data with templates, not by the LLM,
so the benefit amounts and links shown are always exactly what is in the data.
"""

from __future__ import annotations

TEXT = {
    "welcome": {
        "en": "Hello! Tell me a little about yourself: your age, where you live and what work you do.",
        "hi": "नमस्ते! अपने बारे में थोड़ा बताइए: आपकी उम्र, आप कहाँ रहते हैं और क्या काम करते हैं।",
        "mr": "नमस्कार! तुमच्याबद्दल थोडं सांगा: तुमचं वय, तुम्ही कुठे राहता आणि काय काम करता.",
    },
    "not_understood": {
        "en": "Sorry, I didn't get that.",
        "hi": "माफ़ कीजिए, समझ नहीं आया।",
        "mr": "माफ करा, समजलं नाही.",
    },
    "eligible_header": {
        "en": "You may be eligible for these schemes:",
        "hi": "आप इन योजनाओं के लिए पात्र हो सकते हैं:",
        "mr": "तुम्ही या योजनांसाठी पात्र असू शकता:",
    },
    "maybe_header": {
        "en": "These may also apply, but I need more details to be sure:",
        "hi": "ये योजनाएँ भी लागू हो सकती हैं, पर पक्का कहने के लिए और जानकारी चाहिए:",
        "mr": "या योजनाही लागू होऊ शकतात, पण खात्रीसाठी अधिक माहिती हवी:",
    },
    "none_found": {
        "en": "I couldn't find a matching scheme in my list right now.",
        "hi": "अभी मेरी सूची में आपके लिए कोई योजना नहीं मिली।",
        "mr": "सध्या माझ्या यादीत तुमच्यासाठी योग्य योजना सापडली नाही.",
    },
    "benefit": {"en": "Benefit", "hi": "लाभ", "mr": "लाभ"},
    "how_to_apply": {"en": "How to apply", "hi": "आवेदन कैसे करें", "mr": "अर्ज कसा करावा"},
    "documents": {"en": "Documents", "hi": "दस्तावेज़", "mr": "कागदपत्रे"},
    "note": {"en": "Note", "hi": "ध्यान दें", "mr": "लक्षात ठेवा"},
    "link": {"en": "Official site", "hi": "आधिकारिक साइट", "mr": "अधिकृत संकेतस्थळ"},
    "disclaimer": {
        "en": "This is not an official government service. Please confirm on the official website before applying.",
        "hi": "यह सरकारी सेवा नहीं है। आवेदन से पहले आधिकारिक वेबसाइट पर ज़रूर जाँच लें।",
        "mr": "ही अधिकृत सरकारी सेवा नाही. अर्ज करण्यापूर्वी अधिकृत संकेतस्थळावर खात्री करा.",
    },
}


def t(key: str, lang: str) -> str:
    return TEXT[key][lang]


def scheme_card(scheme: dict, lang: str) -> str:
    lines = [
        f"* {scheme['name'][lang]}",
        f"  {t('benefit', lang)}: {scheme['benefit'][lang]}",
        f"  {t('how_to_apply', lang)}: {scheme['how_to_apply'][lang]}",
        f"  {t('documents', lang)}: {', '.join(scheme['documents'])}",
    ]
    for note in scheme.get("also_check", []):
        lines.append(f"  {t('note', lang)}: {note}")
    lines.append(f"  {t('link', lang)}: {scheme['official_url']}")
    return "\n".join(lines)


def results_message(eligible: list[dict], maybe: list[dict], lang: str) -> str:
    parts = []
    if eligible:
        parts.append(t("eligible_header", lang))
        parts += [scheme_card(s, lang) for s in eligible]
    if maybe:
        parts.append(t("maybe_header", lang))
        parts += [f"* {s['name'][lang]}" for s in maybe]
    if not parts:
        parts.append(t("none_found", lang))
    parts.append(t("disclaimer", lang))
    return "\n\n".join(parts)
