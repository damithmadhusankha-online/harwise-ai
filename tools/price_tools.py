
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from utils.validation import ValidationError, validate_crop, validate_positive_int

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"


def _load_rows() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Price file not found: {DATA_FILE}")
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                rows.append({
                    "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    "crop": row["crop"].strip().lower(),
                    "price": float(row["price_per_kg"]),
                })
            except (KeyError, ValueError):
                continue  
    return rows


def get_price_trend(crop: str, days: int = 14, as_of: str | None = None) -> dict:
    try:
        crop = validate_crop(crop)
        days = validate_positive_int(days, "days", max_value=365)
        today = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else date.today()
        rows = _load_rows()
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e)}
    except ValueError:
        return {"ok": False, "error": "as_of must look like YYYY-MM-DD"}

    cutoff = today - timedelta(days=days)
    series = sorted((r for r in rows if r["crop"] == crop and r["date"] >= cutoff),
                    key=lambda r: r["date"])
    # Sample data may be older than "today"; fall back to the latest available window.
    if len(series) < 2:
        all_crop = sorted((r for r in rows if r["crop"] == crop), key=lambda r: r["date"])
        if len(all_crop) < 2:
            return {"ok": False, "error": f"Not enough price history for {crop}."}
        end = all_crop[-1]["date"]
        series = [r for r in all_crop if r["date"] >= end - timedelta(days=days)]
        if len(series) < 2:
            return {"ok": False, "error": f"Not enough price history for {crop} in {days} days."}

    prices = [r["price"] for r in series]
    first, last = prices[0], prices[-1]
    change_pct = round((last - first) / first * 100, 1)
    if change_pct > 3:
        direction = "rising"
    elif change_pct < -3:
        direction = "falling"
    else:
        direction = "flat"

    return {
        "ok": True,
        "crop": crop,
        "period": f"{series[0]['date']} to {series[-1]['date']}",
        "data_points": len(prices),
        "latest_price_per_kg": last,
        "lowest_price_per_kg": min(prices),
        "highest_price_per_kg": max(prices),
        "average_price_per_kg": round(sum(prices) / len(prices), 1),
        "change_percent": change_pct,
        "direction": direction,
        "note": "Sample data. Prices change; treat as a guide, not a guarantee.",
    }
