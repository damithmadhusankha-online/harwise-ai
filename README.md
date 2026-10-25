# Harwise

A locally running AI agent (Ollama + a local LLM) that helps Sri Lankan farmers decide what to
sell, store, and plant across paddy and vegetable crops. All farm data stays on the farmer's device.

> Decision support only. Prices change and the farmer decides. All data in `data/` is **sample data
> and rough assumptions** until replaced with real local figures.

## Setup

```bash
# 1. Install Ollama from https://ollama.com, then pull a tool-calling model
ollama pull qwen2.5:7b        # alternative: llama3.1:8b

# 2. Python deps
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run
python main.py                 # or: python main.py --model llama3.1:8b
```

Commands inside the chat: `reset` clears history, `quit` exits.

## Try these

- `Is the brinjal price rising or falling?`
- `I harvest 3 acres of paddy in 12 days. Moisture about 18%. Should I sell now or store it?`
- `I have 400 kg brinjal and 5000 kg paddy. I need Rs. 60,000 this week. What do I sell first?`
- `Water is low this Yala. What should I plant?`
- `Write a message to a buyer in Sinhala for 3000 kg of paddy.`

## Tools (10)

| Tool | What it does |
|---|---|
| `get_price_trend` | Latest/low/high/average price and direction |
| `get_weather_forecast` | Rain risk (live Open-Meteo, then cache, then sample data) |
| `check_shelf_life` | How long a crop can wait |
| `estimate_yield` | Expected kg from acres |
| `calculate_moisture_penalty` | Paddy price cut and drying cost |
| `compare_sell_options` | Net income for sell now / other market / store, with best and worst case |
| `plan_cash_priority` | What to sell first when cash is tight |
| `suggest_next_season` | Crop ideas from water level and price direction |
| `draft_message` | Buyer/driver message in en, si, ta (templates, have a fluent speaker check si/ta) |
| `save_plan` | Saves the plan to `reports/` |

All arithmetic is in Python, not the LLM. The LLM chooses which tool to call next and explains results.

## Structure

```
main.py            CLI
agent/             loop.py (Ollama tool-calling loop), memory.py, prompts.py
tools/             one file per tool group + registry.py (schemas + safe dispatcher)
utils/             validation.py, logger.py
data/              prices.csv, crops.json, assumptions.json, weather_sample.json   <- edit these
logs/              harwise.log (every user message, tool call, result)
tests/             python tests/run_tests.py   (pytest also works)
```

## Replace sample data (important before the demo)

1. `data/prices.csv`: real paddy and vegetable prices (columns: date, crop, price_per_kg).
2. `data/assumptions.json`: trader discount, drying cost, storage loss, transport. Ask real farmers.
3. `data/crops.json`: shelf life and yields.

## Adding a tool

Write the function (return `{"ok": True/False, ...}`, validate inputs), then add one schema in
`tools/registry.py` `TOOL_SCHEMAS` and one entry in `TOOL_FUNCTIONS`.

## Offline mode

`HARWISE_OFFLINE=1` skips the weather network call and uses cached/sample data.

## Team

| Member | Area |
|---|---|
| Damith Madhusankha | Agent loop, memory, CLI , Planning tools, Tests|
| D.D.A.Nipun | Data layer, validation, price/weather ,messages, logging,|

