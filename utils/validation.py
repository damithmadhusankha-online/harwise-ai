"""Input validation helpers shared by all tools.

Tools never raise to the agent. They return {"ok": False, "error": "..."} so the
LLM can read the problem and correct itself on the next step.
"""
import difflib

KNOWN_CROPS = ["paddy", "brinjal", "long beans", "chillies", "pumpkin"]


class ValidationError(ValueError):
    """Raised by validators; the tool wrapper converts it to an error dict."""


def validate_crop(crop: str, known=KNOWN_CROPS) -> str:
    if not isinstance(crop, str) or not crop.strip():
        raise ValidationError("crop must be a non-empty string")
    name = crop.strip().lower()
    aliases = {"rice": "paddy", "vambatu": "brinjal", "wambatu": "brinjal",
               "beans": "long beans", "mirris": "chillies", "chilli": "chillies"}
    name = aliases.get(name, name)
    if name in known:
        return name
    close = difflib.get_close_matches(name, known, n=2, cutoff=0.6)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    raise ValidationError(f"Unknown crop '{crop}'. Known crops: {', '.join(known)}.{hint}")


def validate_positive_int(value, name: str, max_value: int = 3650) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a whole number, got {value!r}")
    if number <= 0:
        raise ValidationError(f"{name} must be greater than 0, got {number}")
    if number > max_value:
        raise ValidationError(f"{name} must be at most {max_value}, got {number}")
    return number


def validate_choice(value, allowed: list, name: str) -> str:
    text = str(value).strip().lower() if value is not None else ""
    if text not in allowed:
        raise ValidationError(f"{name} must be one of: {', '.join(allowed)}. Got {value!r}")
    return text


def validate_moisture(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"moisture_pct must be a number, got {value!r}")
    if number <= 0 or number > 100:
        raise ValidationError(f"moisture_pct must be between 0 and 100, got {number}")
    return number


def validate_positive_float(value, name: str, max_value: float = 1e9) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number, got {value!r}")
    if number <= 0:
        raise ValidationError(f"{name} must be greater than 0, got {number}")
    if number > max_value:
        raise ValidationError(f"{name} must be at most {max_value}, got {number}")
    return number
