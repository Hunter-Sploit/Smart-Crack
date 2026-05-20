from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".smartcrack"
CONFIG_PATH = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"wordlists": [], "default_wordlist": None}
    return json.loads(CONFIG_PATH.read_text())


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def set_default_wordlist(path: str) -> None:
    cfg = load_config()
    if path not in cfg["wordlists"]:
        cfg["wordlists"].append(path)
    cfg["default_wordlist"] = path
    save_config(cfg)
