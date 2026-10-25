import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.price_tools import get_price_trend
from tools.registry import run_tool


def test_valid_crop():
    r = get_price_trend("paddy", 14, as_of="2026-10-24")
    assert r["ok"] and r["direction"] == "rising"
    assert r["lowest_price_per_kg"] <= r["average_price_per_kg"] <= r["highest_price_per_kg"]


def test_alias_rice_maps_to_paddy():
    assert get_price_trend("rice", 14, as_of="2026-10-24")["crop"] == "paddy"


def test_unknown_crop_gives_suggestion():
    r = get_price_trend("brinjall")
    assert not r["ok"] and "brinjal" in r["error"]


def test_negative_days_rejected():
    assert not get_price_trend("paddy", -5)["ok"]


def test_bad_date_rejected():
    assert not get_price_trend("paddy", 14, as_of="24/10/2026")["ok"]


def test_dispatcher_unknown_tool():
    assert not run_tool("does_not_exist", {})["ok"]


def test_dispatcher_json_string_args():
    assert run_tool("get_price_trend", '{"crop": "pumpkin", "days": 14}')["ok"]


def test_dispatcher_bad_args_do_not_crash():
    assert not run_tool("get_price_trend", {"wrong": 1})["ok"]
