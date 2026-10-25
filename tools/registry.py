import json

from tools.crop_tools import calculate_moisture_penalty, check_shelf_life, estimate_yield
from tools.message_tools import draft_message, save_plan
from tools.planning_tools import compare_sell_options, plan_cash_priority
from tools.price_tools import get_price_trend
from tools.season_tools import suggest_next_season
from tools.weather_tools import get_weather_forecast
from utils.logger import get_logger

log = get_logger("harwise.tools")

CROP_DESC = "paddy (rice), brinjal, long beans, chillies or pumpkin"


def _schema(name, description, properties, required):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


TOOL_SCHEMAS = [
    _schema("get_price_trend",
            "Recent market price per kg for a crop: latest, lowest, highest, average and direction.",
            {"crop": {"type": "string", "description": CROP_DESC},
             "days": {"type": "integer", "description": "Past days to look at. Default 14."}},
            ["crop"]),
    _schema("get_weather_forecast",
            "Rain forecast and a rain_risk level (low/medium/high) for harvest and drying. Use its rain_risk in other tools.",
            {"location": {"type": "string", "description": "polonnaruwa, anuradhapura, kandy or batticaloa. Default polonnaruwa."},
             "days": {"type": "integer", "description": "1 to 7 days. Default 7."}},
            []),
    _schema("check_shelf_life",
            "How many days a crop can be kept before it spoils, and how urgent selling is.",
            {"crop": {"type": "string", "description": CROP_DESC}}, ["crop"]),
    _schema("estimate_yield",
            "Expected harvest in kg from acres. Use the farmer's own yield per acre if they give one.",
            {"crop": {"type": "string", "description": CROP_DESC},
             "acres": {"type": "number", "description": "Land area in acres"},
             "own_yield_kg_per_acre": {"type": "number", "description": "Farmer's own yield, optional"}},
            ["crop", "acres"]),
    _schema("calculate_moisture_penalty",
            "Paddy only. Price cut and drying cost for wet paddy.",
            {"moisture_pct": {"type": "number", "description": "Paddy moisture percent, e.g. 18"},
             "kg": {"type": "number", "description": "Paddy weight in kg"},
             "rain_risk": {"type": "string", "description": "low, medium or high"}},
            ["moisture_pct", "kg"]),
    _schema("compare_sell_options",
            "Compare net income for selling now, selling at another market, or waiting/storing, with best and worst cases. Main decision tool for ONE crop.",
            {"crop": {"type": "string", "description": CROP_DESC},
             "kg": {"type": "number", "description": "Quantity in kg"},
             "moisture_pct": {"type": "number", "description": "Paddy moisture percent, optional"},
             "wait_days": {"type": "integer", "description": "How many days the farmer could wait. Default 14."},
             "rain_risk": {"type": "string", "description": "low, medium or high, from get_weather_forecast"},
             "own_cost_per_kg": {"type": "number", "description": "Farmer's production cost per kg, optional"},
             "pmb_price_per_kg": {"type": "number", "description": "Current Paddy Marketing Board price if the farmer knows it, optional"}},
            ["crop", "kg"]),
    _schema("plan_cash_priority",
            "When the farmer has several crops and needs cash, decide what to sell first and what can wait.",
            {"items": {"type": "array", "description": "Crops the farmer has ready",
                       "items": {"type": "object", "properties": {
                           "crop": {"type": "string"}, "kg": {"type": "number"}}}},
             "cash_needed": {"type": "number", "description": "Rupees needed"}},
            ["items", "cash_needed"]),
    _schema("suggest_next_season",
            "Suggest crops for the next season using water level and current price direction.",
            {"water_level": {"type": "string", "description": "low, medium or high"},
             "season": {"type": "string", "description": "yala or maha"},
             "acres": {"type": "number", "description": "Land area, optional"}},
            ["water_level"]),
    _schema("draft_message",
            "Write a short message to a buyer or lorry driver in English (en), Sinhala (si) or Tamil (ta).",
            {"recipient": {"type": "string", "description": "buyer or driver"},
             "purpose": {"type": "string", "description": "buyer: sell_offer or price_dispute. driver: transport_request"},
             "crop": {"type": "string", "description": CROP_DESC},
             "kg": {"type": "number", "description": "Quantity in kg"},
             "language": {"type": "string", "description": "en, si or ta"},
             "when": {"type": "string", "description": "e.g. 'in 10 days' or 'tomorrow'"}},
            ["recipient", "purpose", "crop", "kg"]),
    _schema("save_plan",
            "Save the final plan as a markdown file the farmer can keep. Only when asked.",
            {"title": {"type": "string"}, "content": {"type": "string", "description": "The plan text"}},
            ["title", "content"]),
]

TOOL_FUNCTIONS = {
    "get_price_trend": get_price_trend,
    "get_weather_forecast": get_weather_forecast,
    "check_shelf_life": check_shelf_life,
    "estimate_yield": estimate_yield,
    "calculate_moisture_penalty": calculate_moisture_penalty,
    "compare_sell_options": compare_sell_options,
    "plan_cash_priority": plan_cash_priority,
    "suggest_next_season": suggest_next_season,
    "draft_message": draft_message,
    "save_plan": save_plan,
}


def run_tool(name: str, arguments) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        log.warning("unknown tool requested: %s", name)
        return {"ok": False, "error": f"Unknown tool '{name}'. Available: {', '.join(TOOL_FUNCTIONS)}"}

    if isinstance(arguments, str): 
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return {"ok": False, "error": "Tool arguments were not valid JSON."}
    if not isinstance(arguments, dict):
        arguments = {}

    log.info("TOOL CALL %s args=%s", name, arguments)
    try:
        result = func(**arguments)
    except TypeError as e:  
        result = {"ok": False, "error": f"Bad arguments for {name}: {e}"}
    except Exception as e:  
        log.exception("tool %s crashed", name)
        result = {"ok": False, "error": f"{name} failed unexpectedly: {e}"}
    log.info("TOOL RESULT %s -> %s", name, result)
    return result
