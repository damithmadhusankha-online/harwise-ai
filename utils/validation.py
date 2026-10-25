"""Input validation helpers shared by all tools.

Validators raise ValidationError for invalid inputs.
Tool wrappers convert these errors into dictionaries so the
agent can understand the issue and retry with valid inputs.
"""

import difflib
import math


KNOWN_CROPS = ["paddy", "brinjal", "long beans", "chillies", "pumpkin"]

CROP_ALIASES = {
    "rice": "paddy",
    "vambatu": "brinjal",
    "wambatu": "brinjal",
    "beans": "long beans",
    "mirris": "chillies",
    "chilli": "chillies",
}


class ValidationError(ValueError):
    """Raised when a tool receives invalid input."""


def _normalize_text(value: str) -> str:
    """Remove extra whitespace and normalize text case."""
    return " ".join(value.strip().lower().split())


def validate_crop(crop: str, known=KNOWN_CROPS) -> str:
    """Validate crop names and resolve supported aliases."""
    if not isinstance(crop, str) or not crop.strip():
        raise ValidationError("crop must be a non-empty string")

    name = _normalize_text(crop)
    name = CROP_ALIASES.get(name, name)

    if name in known:
        return name

    close = difflib.get_close_matches(
        name, known, n=2, cutoff=0.6
    )
    hint = f" Did you mean: {', '.join(close)}?" if close else ""

    raise ValidationError(
        f"Unknown crop '{crop}'. "
        f"Known crops: {', '.join(known)}.{hint}"
    )


def validate_positive_int(value, name: str, max_value: int = 3650) -> int:
    """Validate a positive whole number within the allowed limit."""
    if isinstance(value, bool):
        raise ValidationError(
            f"{name} must be a whole number, got {value!r}"
        )

    try:
        number = int(value)
        numeric_value = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(
            f"{name} must be a whole number, got {value!r}"
        )

    if not math.isfinite(numeric_value) or number != numeric_value:
        raise ValidationError(
            f"{name} must be a whole number, got {value!r}"
        )

    if number <= 0:
        raise ValidationError(
            f"{name} must be greater than 0, got {number}"
        )

    if number > max_value:
        raise ValidationError(
            f"{name} must be at most {max_value}, got {number}"
        )

    return number


def validate_choice(value, allowed: list, name: str) -> str:
    """Validate a choice using case-insensitive matching."""
    text = _normalize_text(str(value)) if value is not None else ""

    normalized_allowed = {
        _normalize_text(str(option))
        for option in allowed
    }

    if text not in normalized_allowed:
        raise ValidationError(
            f"{name} must be one of: {', '.join(map(str, allowed))}. "
            f"Got {value!r}"
        )

    return text


def validate_moisture(value) -> float:
    """Validate moisture percentage between 0 and 100."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(
            f"moisture_pct must be a number, got {value!r}"
        )

    if not math.isfinite(number):
        raise ValidationError(
            "moisture_pct must be a finite number"
        )

    if number <= 0 or number > 100:
        raise ValidationError(
            f"moisture_pct must be between 0 and 100, got {number}"
        )

    return number


def validate_positive_float(
    value, name: str, max_value: float = 1e9
) -> float:
    """Validate a positive finite number within the allowed limit."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(
            f"{name} must be a number, got {value!r}"
        )

    if not math.isfinite(number):
        raise ValidationError(
            f"{name} must be a finite number"
        )

    if number <= 0:
        raise ValidationError(
            f"{name} must be greater than 0, got {number}"
        )

    if number > max_value:
        raise ValidationError(
            f"{name} must be at most {max_value}, got {number}"
        )

    return number
