
from tools.common import load_crops
from tools.price_tools import get_price_trend
from utils.validation import ValidationError, validate_choice, validate_positive_float

WATER_RANK = {"low": 1, "medium": 2, "high": 3}


def suggest_next_season(water_level: str, season: str = "yala", acres: float | None = None) -> dict:
    try:
        water_level = validate_choice(water_level, ["low", "medium", "high"], "water_level")
        season = validate_choice(season, ["yala", "maha"], "season")
        if acres is not None:
            acres = validate_positive_float(acres, "acres", 10_000)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}

    candidates = []
    for crop, info in load_crops().items():
        need = info["water_need"]
        fits = WATER_RANK[need] <= WATER_RANK[water_level]
        trend = get_price_trend(crop, 14)
        direction = trend["direction"] if trend["ok"] else "unknown"
        score = (2 if fits else -5) + {"rising": 1, "flat": 0, "falling": -1, "unknown": 0}[direction]
        reasons = [f"needs {need} water; you have {water_level}"]
        reasons.append(f"recent price is {direction}")
        if not fits:
            reasons.append("water is likely not enough")
        candidates.append({"crop": crop, "water_need": need, "fits_water": fits,
                           "price_direction": direction, "duration_days": info["duration_days"],
                           "score": score, "reasons": reasons})
    candidates.sort(key=lambda c: c["score"], reverse=True)

    warnings = []
    top = [c for c in candidates[:3] if c["fits_water"]]
    if any(c["crop"] == "paddy" for c in top) and len(top) > 1 and water_level != "high":
        warnings.append("Paddy and vegetables may compete for the same irrigation water. Plan the water schedule first.")
    if season == "yala":
        warnings.append("Yala is usually the drier season. Confirm irrigation water with your tank or scheme before planting paddy.")
    return {
        "ok": True, "season": season, "water_level": water_level, "acres": acres,
        "suggestions": candidates, "warnings": warnings,
        "note": "Rule-based guide using current price direction, which can change before harvest. Check with your agrarian services officer.",
    }
