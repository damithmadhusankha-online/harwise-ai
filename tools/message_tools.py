
import re
from datetime import datetime
from pathlib import Path

from utils.validation import (ValidationError, validate_choice, validate_crop,
                              validate_positive_float)

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"

CROP_NAMES = {
    "en": {"paddy": "paddy", "brinjal": "brinjal", "long beans": "long beans",
           "chillies": "chillies", "pumpkin": "pumpkin"},
    "si": {"paddy": "වී", "brinjal": "වම්බටු", "long beans": "මෑ",
           "chillies": "මිරිස්", "pumpkin": "වට්ටක්කා"},
    "ta": {"paddy": "நெல்", "brinjal": "கத்தரிக்காய்", "long beans": "போஞ்சி",
           "chillies": "மிளகாய்", "pumpkin": "பூசணிக்காய்"},
}

TEMPLATES = {
    ("buyer", "sell_offer"): {
        "en": "Hello, I have about {kg} kg of {crop} ready {when}. What price per kg can you offer? Please let me know. Thank you.",
        "si": "ආයුබෝවන්, මා ළඟ {crop} කිලෝ {kg} ක් පමණ {when} සූදානම්. කිලෝවකට ඔබට දිය හැකි මිල කීයද? කරුණාකර දන්වන්න. ස්තූතියි.",
        "ta": "வணக்கம், என்னிடம் சுமார் {kg} கிலோ {crop} {when} தயாராக இருக்கும். ஒரு கிலோவுக்கு நீங்கள் என்ன விலை தர முடியும்? தயவுசெய்து தெரிவிக்கவும். நன்றி.",
    },
    ("buyer", "price_dispute"): {
        "en": "Hello, thank you for your offer for my {crop}. The current market price looks higher. Can you improve the price for {kg} kg? Thank you.",
        "si": "ආයුබෝවන්, මගේ {crop} සඳහා ඔබේ මිලට ස්තූතියි. දැනට වෙළඳපොළ මිල වැඩි බව පෙනේ. කිලෝ {kg} ක් සඳහා මිල තව ටිකක් වැඩි කළ හැකිද? ස්තූතියි.",
        "ta": "வணக்கம், என் {crop} க்கு நீங்கள் கூறிய விலைக்கு நன்றி. தற்போதைய சந்தை விலை அதிகமாகத் தெரிகிறது. {kg} கிலோவுக்கு விலையை சற்று உயர்த்த முடியுமா? நன்றி.",
    },
    ("driver", "transport_request"): {
        "en": "Hello, I need a lorry to carry about {kg} kg of {crop} {when}. What is the charge? Thank you.",
        "si": "ආයුබෝවන්, {crop} කිලෝ {kg} ක් පමණ {when} ප්‍රවාහනය කිරීමට ලොරියක් අවශ්‍යයි. ගාස්තුව කීයද? ස්තූතියි.",
        "ta": "வணக்கம், சுமார் {kg} கிலோ {crop} ஐ {when} ஏற்றிச் செல்ல லாரி தேவை. கட்டணம் எவ்வளவு? நன்றி.",
    },
}


def draft_message(recipient: str, purpose: str, crop: str, kg: float,
                  language: str = "en", when: str = "soon") -> dict:
    try:
        recipient = validate_choice(recipient, ["buyer", "driver"], "recipient")
        language = validate_choice(language, ["en", "si", "ta"], "language")
        crop = validate_crop(crop)
        kg = validate_positive_float(kg, "kg", 1_000_000)
        purpose = validate_choice(purpose, sorted({p for (r, p) in TEMPLATES if r == recipient}), "purpose")
        when = str(when).strip()[:40] or "soon"
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    tpl = TEMPLATES.get((recipient, purpose))
    if tpl is None:
        return {"ok": False, "error": f"No template for recipient={recipient}, purpose={purpose}"}
    text = tpl[language].format(kg=round(kg), crop=CROP_NAMES[language][crop], when=when)
    result = {"ok": True, "language": language, "message": text}
    if language != "en":
        result["note"] = "Template-based. Ask a fluent speaker to check it before sending."
    return result


def save_plan(title: str, content: str) -> dict:
    if not isinstance(title, str) or not title.strip():
        return {"ok": False, "error": "title must be a non-empty string"}
    if not isinstance(content, str) or not content.strip():
        return {"ok": False, "error": "content must be a non-empty string"}
    if len(content) > 20_000:
        return {"ok": False, "error": "content is too long (max 20000 characters)"}
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "plan"
    try:
        REPORT_DIR.mkdir(exist_ok=True)
        path = REPORT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}.md"
        path.write_text(f"# {title.strip()}\n\n{content.strip()}\n\n---\nDecision support only. Prices change; the farmer decides.\n",
                        encoding="utf-8")
    except OSError as e:
        return {"ok": False, "error": f"Could not save the plan: {e}"}
    return {"ok": True, "saved_to": str(path)}
