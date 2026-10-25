import os
import sys
from pathlib import Path

os.environ["HARWISE_OFFLINE"] = "1" 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.crop_tools import calculate_moisture_penalty, check_shelf_life, estimate_yield
from tools.message_tools import draft_message, save_plan
from tools.planning_tools import compare_sell_options, plan_cash_priority
from tools.registry import TOOL_FUNCTIONS, TOOL_SCHEMAS, run_tool
from tools.season_tools import suggest_next_season
from tools.weather_tools import get_weather_forecast


def test_every_schema_has_a_function():
    names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert names == set(TOOL_FUNCTIONS)
    assert len(names) >= 4


def test_shelf_life():
    assert check_shelf_life("brinjal")["shelf_life_days"] < 10
    assert not check_shelf_life("banana")["ok"]


def test_yield():
    r = estimate_yield("paddy", 3)
    assert r["ok"] and r["low_estimate_kg"] < r["expected_total_kg"] < r["high_estimate_kg"]
    assert estimate_yield("paddy", 3, own_yield_kg_per_acre=2000)["expected_total_kg"] == 6000
    assert not estimate_yield("paddy", -1)["ok"]


def test_moisture():
    r = calculate_moisture_penalty(14, 1000)
    assert r["buyer_price_cut_pct"] == 0 and r["total_drying_cost"] == 0
    wet = calculate_moisture_penalty(20, 1000, "high")
    assert wet["buyer_price_cut_pct"] == 9.0 and wet["drying_cost_per_kg"] > calculate_moisture_penalty(20, 1000)["drying_cost_per_kg"]
    assert not calculate_moisture_penalty(150, 1000)["ok"]
    assert not calculate_moisture_penalty(18, 0)["ok"]


def test_weather_offline_sample():
    r = get_weather_forecast("polonnaruwa", 7)
    assert r["ok"] and r["rain_risk"] in {"low", "medium", "high"}
    # offline mode uses a saved forecast if one exists, otherwise the sample data
    assert "sample" in r["source"] or "cached" in r["source"]
    assert not get_weather_forecast("mars")["ok"]
    assert not get_weather_forecast("kandy", 20)["ok"]


def test_compare_paddy():
    r = compare_sell_options("paddy", 5000, moisture_pct=18, wait_days=21, pmb_price_per_kg=120)
    assert r["ok"]
    names = [o["option"] for o in r["options"]]
    assert "sell_now_to_trader" in names and "sell_to_pmb" in names and "dry_and_store_21_days" in names
    for o in r["options"]:
        assert o["worst_case_net_total"] <= o["expected_net_total"] <= o["best_case_net_total"]


def test_compare_paddy_warns_when_moisture_or_pmb_missing():
    r = compare_sell_options("paddy", 1000)
    assert r["ok"] and len(r["warnings"]) == 2


def test_compare_vegetable_wait_not_feasible():
    r = compare_sell_options("long beans", 300, wait_days=10)
    assert r["ok"]
    waits = [o for o in r["options"] if o["option"].startswith("wait")]
    assert waits and waits[0]["feasible"] is False
    assert r["highest_expected_option"] in {"sell_local_now", "sell_at_dambulla"}


def test_rain_reduces_dambulla_result():
    low = compare_sell_options("brinjal", 400, rain_risk="low")
    high = compare_sell_options("brinjal", 400, rain_risk="high")
    pick = lambda r: next(o for o in r["options"] if o["option"] == "sell_at_dambulla")["expected_net_total"]
    assert pick(high) < pick(low)


def test_compare_validation():
    assert not compare_sell_options("paddy", -5)["ok"]
    assert not compare_sell_options("paddy", 100, rain_risk="storm")["ok"]
    assert not compare_sell_options("mango", 100)["ok"]


def test_cash_priority():
    r = plan_cash_priority([{"crop": "paddy", "kg": 5000}, {"crop": "brinjal", "kg": 400}], 40000)
    assert r["ok"]
    assert r["plan"][0]["crop"] == "brinjal" and r["plan"][0]["action"] == "sell_soon"
    assert not plan_cash_priority([], 1000)["ok"]
    assert not plan_cash_priority([{"crop": "paddy", "kg": 10}], -1)["ok"]
    assert not plan_cash_priority("paddy", 1000)["ok"]


def test_cash_priority_can_wait_when_covered():
    r = plan_cash_priority([{"crop": "paddy", "kg": 5000}, {"crop": "pumpkin", "kg": 500}], 1000)
    pump = next(p for p in r["plan"] if p["crop"] == "pumpkin")
    paddy = next(p for p in r["plan"] if p["crop"] == "paddy")
    assert pump["action"] == "sell_soon" and paddy["action"] == "can_wait"


def test_next_season():
    low = suggest_next_season("low", "yala")
    assert low["ok"] and next(c for c in low["suggestions"] if c["crop"] == "paddy")["fits_water"] is False
    assert suggest_next_season("high", "maha")["suggestions"][0]["fits_water"]
    assert not suggest_next_season("plenty")["ok"]


def test_messages():
    for lang in ("en", "si", "ta"):
        r = draft_message("buyer", "sell_offer", "paddy", 3000, lang, "in 10 days")
        assert r["ok"] and "3000" in r["message"]
    assert not draft_message("buyer", "transport_request", "paddy", 100)["ok"]
    assert not draft_message("cousin", "sell_offer", "paddy", 100)["ok"]
    assert not draft_message("buyer", "sell_offer", "paddy", 100, "fr")["ok"]


def test_save_plan(tmp_path=None):
    r = save_plan("Test plan", "Sell brinjal first.")
    assert r["ok"] and Path(r["saved_to"]).exists()
    Path(r["saved_to"]).unlink()
    assert not save_plan("", "x")["ok"]
    assert not save_plan("t", "x" * 30_000)["ok"]


def test_dispatcher_nested_args_and_errors():
    r = run_tool("plan_cash_priority", {"items": [{"crop": "rice", "kg": 100}], "cash_needed": 5000})
    assert r["ok"]
    assert not run_tool("compare_sell_options", {"crop": "paddy"})["ok"]  # missing kg