from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SMARTCRACK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_wordlist: str | None = Field(default=None, description="Default wordlist path")
    wordlists: list[str] = Field(default_factory=list, description="List of known wordlists")
    preferred_tool: str | None = Field(default=None, description="Preferred cracking tool: hashcat or john")
    timeout_seconds: int = Field(default=3600, ge=60, description="Default timeout in seconds")
    session_dir: str = Field(default_factory=lambda: str(Path.home() / ".smartcrack" / "sessions"))


CONFIG_DIR = Path.home() / ".smartcrack"
CONFIG_PATH = CONFIG_DIR / "config.json"

_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = _load_or_migrate()
    return _settings


def _load_or_migrate() -> Settings:
    if CONFIG_PATH.exists():
        try:
            old = json.loads(CONFIG_PATH.read_text())
            return Settings(
                default_wordlist=old.get("default_wordlist"),
                wordlists=old.get("wordlists", []),
                preferred_tool=old.get("preferred_backend"),
                timeout_seconds=old.get("timeout_seconds", 3600),
                session_dir=old.get("session_dir", str(CONFIG_DIR / "sessions")),
            )
        except (json.JSONDecodeError, OSError):
            pass
    return Settings()


def save_settings(settings: Settings) -> None:
    global _settings
    _settings = settings
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(settings.model_dump(), indent=2))


def reset_settings() -> Settings:
    global _settings
    _settings = Settings()
    save_settings(_settings)
    return _settings


def load_config() -> dict:
    return get_settings().model_dump()


def set_default_wordlist(path: str) -> None:
    settings = get_settings()
    settings.default_wordlist = path
    if path not in settings.wordlists:
        settings.wordlists.append(path)
    save_settings(settings)


def reset_config() -> dict:
    return reset_settings().model_dump()