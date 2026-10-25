import csv
import math
from datetime import date, datetime, timedelta
from pathlib import Path

from utils.validation import ValidationError, validate_crop, validate_positive_int

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"


def _load_rows() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Price file not found: {DATA_FILE}")

    records = {}

    with DATA_FILE.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"date", "crop", "price_per_kg"}

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                "Price CSV must contain date, crop, and price_per_kg columns"
            )

        for row in reader:
            try:
                record_date = datetime.strptime(
                    row["date"], "%Y-%m-%d"
                ).date()

                crop = row["crop"].strip().lower()
                price = float(row["price_per_kg"])

                # Ignore missing, invalid, or unrealistic price values.
                if not crop or not math.isfinite(price) or price <= 0:
                    continue

            except (TypeError, ValueError, AttributeError):
                continue

            # Keep the latest record for each crop and date.
            records[(crop, record_date)] = {
                "date": record_date,
                "crop": crop,
                "price": price,
            }

    return list(records.values())


def get_price_trend(crop: str, days: int = 14, as_of: str | None = None) -> dict:
    try:
        crop = validate_crop(crop)
        days = validate_positive_int(days, "days", max_value=365)

        today = (
            datetime.strptime(as_of, "%Y-%m-%d").date()
            if as_of else date.today()
        )

        rows = _load_rows()

    except ValidationError as e:
        return {"ok": False, "error": str(e)}

    except OSError as e:
        return {
            "ok": False,
            "error": f"Unable to read price data: {e}",
        }

    except ValueError as e:
        if as_of:
            try:
                datetime.strptime(as_of, "%Y-%m-%d")
            except (TypeError, ValueError):
                return {
                    "ok": False,
                    "error": "as_of must look like YYYY-MM-DD",
                }

        return {"ok": False, "error": str(e)}

    cutoff = today - timedelta(days=days)

    series = sorted(
        (
            row for row in rows
            if row["crop"] == crop and row["date"] >= cutoff
        ),
        key=lambda row: row["date"],
    )

    # Fall back to the latest available historical data.
    if len(series) < 2:
        all_crop = sorted(
            (row for row in rows if row["crop"] == crop),
            key=lambda row: row["date"],
        )

        if len(all_crop) < 2:
            return {
                "ok": False,
                "error": f"Not enough price history for {crop}.",
            }

        end = all_crop[-1]["date"]

        series = [
            row for row in all_crop
            if row["date"] >= end - timedelta(days=days)
        ]

        if len(series) < 2:
            return {
                "ok": False,
                "error": f"Not enough price history for {crop} in {days} days.",
            }

    prices = [row["price"] for row in series]

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
