from __future__ import annotations

import json
from pathlib import Path

from smartcrack.config.settings import Settings, reset_settings, save_settings

CONFIG_DIR = Path.home() / ".smartcrack"
CONFIG_PATH = CONFIG_DIR / "config.json"


def migrate_legacy_config() -> Settings:
    """Migrate from old JSON config to Pydantic Settings."""
    if not CONFIG_PATH.exists():
        return Settings()

    try:
        old = json.loads(CONFIG_PATH.read_text())
        settings = Settings(
            default_wordlist=old.get("default_wordlist"),
            wordlists=old.get("wordlists", []),
            preferred_tool=old.get("preferred_backend"),
            timeout_seconds=old.get("timeout_seconds", 3600),
            session_dir=old.get("session_dir", str(CONFIG_DIR / "sessions")),
        )
        save_settings(settings)
        return settings
    except (json.JSONDecodeError, OSError):
        return Settings()


def load_config() -> dict:
    """Compatibility wrapper for old dict-based config access."""
    settings = migrate_legacy_config()
    return settings.model_dump()


def set_default_wordlist(path: str) -> None:
    settings = migrate_legacy_config()
    settings.default_wordlist = path
    if path not in settings.wordlists:
        settings.wordlists.append(path)
    save_settings(settings)


def reset_config() -> dict:
    settings = reset_settings()
    return settings.model_dump()