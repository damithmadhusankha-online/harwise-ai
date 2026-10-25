from tools.common import load_assumptions, load_crops
from tools.crop_tools import calculate_moisture_penalty
from tools.price_tools import get_price_trend
from utils.validation import (ValidationError, validate_choice, validate_crop,
                              validate_moisture, validate_positive_float,
                              validate_positive_int)


def _opt(name, unit_exp, unit_best, unit_worst, kg, own_cost, notes, feasible=True):
    def total(u):
        return round(u * kg - (own_cost or 0) * kg)
    return {
        "option": name, "feasible": feasible,
        "expected_net_total": total(unit_exp), "best_case_net_total": total(unit_best),
        "worst_case_net_total": total(unit_worst),
        "expected_net_per_kg": round(unit_exp - (own_cost or 0), 2),
        "notes": notes,
    }


def compare_sell_options(crop: str, kg: float, moisture_pct: float | None = None,
                         wait_days: int = 14, rain_risk: str = "low",
                         own_cost_per_kg: float | None = None,
                         pmb_price_per_kg: float | None = None) -> dict:
    try:
        crop = validate_crop(crop)
        kg = validate_positive_float(kg, "kg", 1_000_000)
        wait_days = validate_positive_int(wait_days, "wait_days", 120)
        rain_risk = validate_choice(rain_risk, ["low", "medium", "high"], "rain_risk")
        if moisture_pct is not None:
            moisture_pct = validate_moisture(moisture_pct)
        if own_cost_per_kg is not None:
            own_cost_per_kg = validate_positive_float(own_cost_per_kg, "own_cost_per_kg", 100_000)
        if pmb_price_per_kg is not None:
            pmb_price_per_kg = validate_positive_float(pmb_price_per_kg, "pmb_price_per_kg", 100_000)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}

    trend = get_price_trend(crop, 14)
    if not trend["ok"]:
        return trend
    latest, low, high = trend["latest_price_per_kg"], trend["lowest_price_per_kg"], trend["highest_price_per_kg"]
    a = load_assumptions()
    info = load_crops()[crop]
    rain_mult = a["rain_multiplier"][rain_risk]
    options, warnings = [], []
    scen = (latest, high, low)  # expected, best, worst

    if info["type"] == "paddy":
        p = a["paddy"]
        assumed = moisture_pct is None
        moisture = moisture_pct if moisture_pct is not None else p["default_harvest_moisture_pct"]
        if assumed:
            warnings.append(f"Moisture not given; assumed {moisture}%. Ask the farmer or measure it.")
        pen = calculate_moisture_penalty(moisture, kg, rain_risk)
        cut = pen["buyer_price_cut_pct"] / 100
        td = p["trader_discount_pct"] / 100

        u = [x * (1 - td) * (1 - cut) for x in scen]
        options.append(_opt("sell_now_to_trader", *u, kg, own_cost_per_kg,
                            [f"Trader discount {p['trader_discount_pct']}% and moisture cut {pen['buyer_price_cut_pct']}% applied."]))

        if pmb_price_per_kg:
            unit = pmb_price_per_kg * (1 - cut) - p["pmb_transport_cost_per_kg"]
            options.append(_opt("sell_to_pmb", unit, unit, unit, kg, own_cost_per_kg,
                                ["Fixed price given by farmer. Confirm PMB is buying, quantity limits and payment delay."]))
        else:
            warnings.append("No PMB price given, so PMB option was skipped. Ask the farmer for the current PMB price.")

        weeks = wait_days / 7
        loss = min(50.0, weeks * p["storage_loss_pct_per_week"])
        drying = pen["drying_cost_per_kg"]
        storage = weeks * p["storage_cost_per_kg_per_week"]

        def store_unit(price):
            interest = price * (a["interest_rate_pct_per_year"] / 100) * (wait_days / 365)
            return price * (1 - td) * (1 - loss / 100) - drying - storage - interest
        options.append(_opt(f"dry_and_store_{wait_days}_days", *[store_unit(x) for x in scen],
                            kg, own_cost_per_kg,
                            [f"Drying {drying}/kg, storage loss {round(loss, 1)}%, storage cost and interest included.",
                             "Assumes price stays near today's level; storing is a bet on a price rise."]))
    else:
        v = a["vegetable"]
        shelf = info["shelf_life_days"]
        ld = v["local_buyer_discount_pct"] / 100
        options.append(_opt("sell_local_now", *[x * (1 - ld) for x in scen], kg, own_cost_per_kg,
                            [f"Local buyer discount {v['local_buyer_discount_pct']}% applied."]))

        transit = v["dambulla_transit_loss_pct"] * rain_mult / 100
        transport = v["dambulla_transport_cost_per_kg"] * (1.2 if rain_risk == "high" else 1.0)
        options.append(_opt("sell_at_dambulla", *[x * (1 + v["dambulla_premium_pct"] / 100) * (1 - transit) - transport
                                                  for x in scen], kg, own_cost_per_kg,
                            [f"Premium {v['dambulla_premium_pct']}% minus transport {round(transport, 1)}/kg and transit loss {round(transit * 100, 1)}%."]))

        if wait_days <= shelf * 0.5:
            spoil = wait_days / shelf * v["spoilage_pct_at_end_of_shelf_life"]
            options.append(_opt(f"wait_{wait_days}_days_then_sell_local",
                                *[x * (1 - ld) * (1 - spoil / 100) for x in scen], kg, own_cost_per_kg,
                                [f"Estimated spoilage {round(spoil, 1)}%. Assumes price stays near today's level."]))
        else:
            options.append({"option": f"wait_{wait_days}_days", "feasible": False,
                            "notes": [f"{crop} lasts about {shelf} days; waiting {wait_days} days is not realistic."]})

    feasible = [o for o in options if o["feasible"]]
    best = max(feasible, key=lambda o: o["expected_net_total"])
    safest = max(feasible, key=lambda o: o["worst_case_net_total"])
    close = [o["option"] for o in feasible if o is not best
             and best["expected_net_total"] > 0
             and o["expected_net_total"] >= 0.95 * best["expected_net_total"]]
    return {
        "ok": True, "crop": crop, "kg": kg, "price_window": trend["period"],
        "latest_price_per_kg": latest, "rain_risk_used": rain_risk,
        "options": options,
        "highest_expected_option": best["option"],
        "safest_option_by_worst_case": safest["option"],
        "close_alternatives": close,
        "farmer_summary": [
            (f"{o['option']}: expected Rs. {o['expected_net_total']:,} "
             f"(worst case Rs. {o['worst_case_net_total']:,}, best case Rs. {o['best_case_net_total']:,})")
            if o["feasible"] else f"{o['option']}: not realistic. {o['notes'][0]}"
            for o in options],
        "warnings": warnings,
        "note": "Estimates from sample prices and editable assumptions. Present best and worst cases; do not promise outcomes.",
    }


def plan_cash_priority(items: list, cash_needed: float) -> dict:
    """Decide what to sell first when cash is tight. items: [{"crop": str, "kg": number}]."""
    try:
        cash_needed = validate_positive_float(cash_needed, "cash_needed", 1e9)
        if not isinstance(items, list) or not items:
            raise ValidationError("items must be a non-empty list of {crop, kg}")
        if len(items) > 20:
            raise ValidationError("Please give at most 20 items")
        parsed = []
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise ValidationError(f"Item {i + 1} must be an object with crop and kg")
            parsed.append((validate_crop(it.get("crop")), validate_positive_float(it.get("kg"), f"item {i + 1} kg", 1_000_000)))
    except ValidationError as e:
        return {"ok": False, "error": str(e)}

    crops = load_crops()
    rows = []
    for crop, kg in parsed:
        trend = get_price_trend(crop, 14)
        if not trend["ok"]:
            return trend
        rows.append({"crop": crop, "kg": kg, "shelf_life_days": crops[crop]["shelf_life_days"],
                     "price_per_kg": trend["latest_price_per_kg"],
                     "gross_value": round(kg * trend["latest_price_per_kg"])})
    rows.sort(key=lambda r: r["shelf_life_days"])  # most perishable first

    raised, plan = 0, []
    for r in rows:
        perishable = r["shelf_life_days"] <= 7
        if raised < cash_needed or perishable:
            action = "sell_soon"
            raised += r["gross_value"]
            reason = "perishable, do not hold" if perishable and raised - r["gross_value"] >= cash_needed else "needed to reach the cash target"
        else:
            action = "can_wait"
            reason = "cash target already covered; this lasts longer, so you can wait for a better price"
        plan.append({**r, "action": action, "reason": reason})
    return {
        "ok": True, "cash_needed": cash_needed, "expected_gross_cash_from_sell_soon": raised,
        "shortfall": max(0, round(cash_needed - raised)),
        "plan": plan,
        "farmer_summary": [
            f"{r['crop']} {r['kg']:.0f} kg is about Rs. {r['gross_value']:,} before costs: {r['action']} ({r['reason']})"
            for r in plan],
        "note": "Gross values at the latest sample price, before transport and buyer discounts. Net cash will be lower.",
    }
