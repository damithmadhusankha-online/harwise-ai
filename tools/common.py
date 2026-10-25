import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> dict:
    """Load and validate a JSON data file."""
    file_path = DATA_DIR / name

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Required data file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {name} at line "
            f"{error.lineno}, column {error.colno}: "
            f"{error.msg}"
        ) from error

    except UnicodeError as error:
        raise ValueError(
            f"Unable to decode data file {name}: {error}"
        ) from error

    except OSError as error:
        raise OSError(
            f"Unable to read data file {name}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid data structure in {name}: "
            "expected a JSON object"
        )

    for key in data:
        if not isinstance(key, str):
            raise ValueError(
                f"Invalid key in {name}: "
                "all keys must be strings"
            )

    return data


def _filter_metadata(data: dict) -> dict:
    """Exclude internal metadata keys beginning with '_'."""
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("_")
    }


def load_crops() -> dict:
    """Load crop information without internal metadata."""
    return _filter_metadata(_load("crops.json"))


def load_assumptions() -> dict:
    """Load farming assumptions without internal metadata."""
    return _filter_metadata(_load("assumptions.json"))
