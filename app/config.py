from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def load_json(name: str, default: Any = None) -> Any:
    path = CONFIG_DIR / name
    if not path.exists():
        return default if default is not None else {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def settings() -> dict[str, Any]:
    return load_json("settings.json", {})


def apps_config() -> list[dict[str, Any]]:
    data = load_json("apps.json", [])
    return data if isinstance(data, list) else []
