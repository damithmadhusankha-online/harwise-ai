from tools.common import load_assumptions, load_crops
from utils.validation import (ValidationError, validate_choice, validate_crop,
                              validate_moisture, validate_positive_float)


def check_shelf_life(crop: str) -> dict:
    try:
        crop = validate_crop(crop)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    info = load_crops()[crop]
    days = info["shelf_life_days"]
    if days <= 7:
        urgency = "very perishable: sell within a few days"
    elif days <= 45:
        urgency = "moderately perishable: can wait a short time"
    else:
        urgency = "stores well if dried and kept dry"
    return {"ok": True, "crop": crop, "type": info["type"], "shelf_life_days": days,
            "urgency": urgency, "note": "Approximate. Depends on handling and storage."}


def estimate_yield(crop: str, acres: float, own_yield_kg_per_acre: float | None = None) -> dict:
    try:
        crop = validate_crop(crop)
        acres = validate_positive_float(acres, "acres", 10_000)
        if own_yield_kg_per_acre is not None:
            own_yield_kg_per_acre = validate_positive_float(own_yield_kg_per_acre,
                                                            "own_yield_kg_per_acre", 100_000)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    default = load_crops()[crop]["yield_kg_per_acre"]
    per_acre = own_yield_kg_per_acre or default
    return {
        "ok": True, "crop": crop, "acres": acres, "yield_kg_per_acre_used": per_acre,
        "expected_total_kg": round(acres * per_acre),
        "low_estimate_kg": round(acres * per_acre * 0.8),
        "high_estimate_kg": round(acres * per_acre * 1.2),
        "source": "farmer's own figure" if own_yield_kg_per_acre else "rough default (replace with your own yield)",
    }


def calculate_moisture_penalty(moisture_pct: float, kg: float, rain_risk: str = "low") -> dict:
    
    try:
        moisture_pct = validate_moisture(moisture_pct)
        kg = validate_positive_float(kg, "kg", 1_000_000)
        rain_risk = validate_choice(rain_risk, ["low", "medium", "high"], "rain_risk")
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    a = load_assumptions()
    p = a["paddy"]
    points_over = max(0.0, moisture_pct - p["standard_moisture_pct"])
    price_cut_pct = min(50.0, points_over * p["moisture_price_cut_pct_per_point"])
    drying_per_kg = points_over * p["drying_cost_per_kg_per_point"] * a["rain_multiplier"][rain_risk]
    return {
        "ok": True, "moisture_pct": moisture_pct,
        "standard_moisture_pct": p["standard_moisture_pct"],
        "points_over_standard": round(points_over, 1),
        "buyer_price_cut_pct": round(price_cut_pct, 1),
        "drying_cost_per_kg": round(drying_per_kg, 2),
        "total_drying_cost": round(drying_per_kg * kg),
        "rain_risk": rain_risk,
        "note": "Uses editable assumptions in data/assumptions.json, not official rates.",
    }
