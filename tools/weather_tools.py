
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime

from tools.common import DATA_DIR
from utils.logger import get_logger
from utils.validation import ValidationError, validate_positive_int

log = get_logger("harwise.weather")

LOCATIONS = {  
    "polonnaruwa": (7.94, 81.02),
    "anuradhapura": (8.31, 80.40),
    "kandy": (7.29, 80.63),
    "batticaloa": (7.71, 81.69),
}
CACHE_FILE = DATA_DIR / "weather_cache.json"


def _risk(max_prob: float, total_mm: float) -> str:
    if max_prob >= 70 or total_mm >= 40:
        return "high"
    if max_prob >= 40 or total_mm >= 15:
        return "medium"
    return "low"


def _fetch_live(lat: float, lon: float, days: int) -> list[dict]:
    qs = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "forecast_days": days,
        "daily": "precipitation_probability_max,precipitation_sum",
        "timezone": "Asia/Colombo",
    })
    with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{qs}", timeout=6) as r:
        d = json.load(r)["daily"]
    return [{"day": i + 1, "rain_prob": d["precipitation_probability_max"][i] or 0,
             "rain_mm": d["precipitation_sum"][i] or 0} for i in range(len(d["time"]))]


def get_weather_forecast(location: str = "polonnaruwa", days: int = 7) -> dict:
    try:
        key = str(location).strip().lower()
        if key not in LOCATIONS:
            raise ValidationError(f"Unknown location '{location}'. Known: {', '.join(LOCATIONS)}")
        days = validate_positive_int(days, "days", 7)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}

    source, forecast = None, None
    if os.environ.get("HARWISE_OFFLINE") != "1":
        try:
            forecast = _fetch_live(*LOCATIONS[key], days)
            source = "live (Open-Meteo)"
            CACHE_FILE.write_text(json.dumps({key: forecast}), encoding="utf-8")
        except Exception as e:
            log.warning("live weather failed: %s", e)
    if forecast is None and CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8")).get(key)
            if cached:
                forecast, source = cached[:days], "cached (may be out of date)"
        except Exception as e:
            log.warning("cache unreadable: %s", e)
    if forecast is None:
        sample = json.loads((DATA_DIR / "weather_sample.json").read_text(encoding="utf-8"))
        forecast = sample.get(key, sample["polonnaruwa"])
        source = "sample data (not a real forecast)"

    forecast = forecast[:days]
    max_prob = max(f["rain_prob"] for f in forecast)
    total_mm = sum(f["rain_mm"] for f in forecast)
    wettest = max(forecast, key=lambda f: f["rain_prob"])
    return {
        "ok": True, "location": key, "days": len(forecast), "source": source,
        "max_rain_probability_pct": max_prob, "total_rain_mm": round(total_mm, 1),
        "wettest_day": wettest["day"], "rain_risk": _risk(max_prob, total_mm),
        "daily": forecast,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
