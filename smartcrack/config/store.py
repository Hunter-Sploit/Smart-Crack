from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".smartcrack"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_SESSION_DIR = CONFIG_DIR / "sessions"


DEFAULT_CONFIG = {
    "wordlists": [],
    "default_wordlist": None,
    "preferred_backend": None,
    "timeout_seconds": 3600,
    "session_dir": str(DEFAULT_SESSION_DIR),
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
        # Merge with defaults to handle config upgrades
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def set_default_wordlist(path: str) -> None:
    cfg = load_config()
    if path not in cfg["wordlists"]:
        cfg["wordlists"].append(path)
    cfg["default_wordlist"] = path
    save_config(cfg)


def set_preferred_backend(backend: str | None) -> None:
    cfg = load_config()
    if backend and backend.lower() in {"hashcat", "john", "auto"}:
        cfg["preferred_backend"] = backend.lower()
    else:
        cfg["preferred_backend"] = None
    save_config(cfg)


def set_timeout(timeout: int) -> None:
    cfg = load_config()
    cfg["timeout_seconds"] = max(60, timeout)  # minimum 1 minute
    save_config(cfg)


def set_session_dir(path: str) -> None:
    cfg = load_config()
    cfg["session_dir"] = str(Path(path).expanduser().resolve())
    save_config(cfg)


def reset_config() -> dict:
    save_config(DEFAULT_CONFIG.copy())
    return DEFAULT_CONFIG.copy()
