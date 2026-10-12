from __future__ import annotations

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


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def save_settings(settings: Settings) -> None:
    global _settings
    _settings = settings
    _persist_to_json(settings)


def _persist_to_json(settings: Settings) -> None:
    config_dir = Path.home() / ".smartcrack"
    config_path = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    data = settings.model_dump()
    config_path.write_text(json.dumps(data, indent=2))


def reset_settings() -> Settings:
    global _settings
    _settings = Settings()
    _persist_to_json(_settings)
    return _settings


import json