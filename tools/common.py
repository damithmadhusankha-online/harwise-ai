import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_crops() -> dict:
    return {k: v for k, v in _load("crops.json").items() if not k.startswith("_")}


def load_assumptions() -> dict:
    return {k: v for k, v in _load("assumptions.json").items() if not k.startswith("_")}
