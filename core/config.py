from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_file = path or CONFIG_PATH
    with config_file.open(encoding="utf-8") as file:
        return yaml.safe_load(file)
