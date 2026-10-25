# Harwise

A locally running AI agent (Ollama + a local LLM) that helps Sri Lankan farmers decide what to
sell, store, and plant across paddy and vegetable crops. All farm data stays on the farmer's device.

> Decision support only. Prices change and the farmer decides. All data in `data/` is **sample data
> and rough assumptions** until replaced with real local figures.

## Setup


## Setup

1. Install [Ollama](https://ollama.com) and pull a tool-calling model:

   ```bash
   ollama pull qwen2.5:7b
   ```

   Alternative models:

   ```bash
   ollama pull llama3.1:8b
   ollama pull llama3.2
   ```

2. Create and activate a Python virtual environment:

   **Windows PowerShell:**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   **Linux/macOS:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run Harwise:

   ```bash
   python main.py
   ```

   Or select an alternative model:

   ```bash
   python main.py --model llama3.1:8b
   python main.py --model llama3.2
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


## Reliability and Data Validation

Harwise includes validation, error handling, and local data management to improve the reliability of its farming recommendations.

### Price Data Processing
- Reads historical crop prices from `data/prices.csv`.
- Validates price records and rejects invalid or non-positive values.
- Handles duplicate crop/date entries and malformed CSV data.
- Calculates price trends using validated historical records.

### Weather Data Management
- Retrieves weather forecasts from Open-Meteo when available.
- Uses cached or sample weather data when live information is unavailable.
- Preserves previously cached locations when updating the weather cache.
- Supports offline weather lookup using `HARWISE_OFFLINE=1`.

### Input Validation
- Normalizes text inputs and supports recognized crop-name aliases.
- Validates numeric inputs, including quantities and moisture percentages.
- Rejects invalid, non-finite, or unsupported input values.

### Message and Report Handling
- Supports buyer and driver message templates in English, Sinhala, and Tamil.
- Validates message inputs while preserving decimal quantities.
- Validates report titles and content before saving.
- Uses unique report filenames to avoid overwriting existing plans.

### Logging
- Records application activity for debugging and troubleshooting.
- Uses rotating log files to limit disk usage.
- Keeps up to three backup log files, with a maximum of 5 MB per active log file.

### JSON Data Loading
- Loads crop information and farming assumptions from local JSON files.
- Detects missing files, malformed JSON, and invalid top-level data structures.
- Excludes internal metadata fields from the loaded data.

### Testing

Run the project's test suite:

```bash
python tests/run_tests.py
```

These improvements strengthen data handling and application reliability. They do not replace the need to verify sample prices, crop assumptions, weather information, or generated recommendations against real local conditions.


## Team

| Member | Area |
|---|---|
| Damith Madhusankha | Agent loop, memory, CLI , Planning tools, Tests|
| D.D.A.Nipun | Data layer, validation, price/weather ,messages, logging,|

# harwise-ai
# harwise-ai
