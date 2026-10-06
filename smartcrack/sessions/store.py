from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SESSION_DIR = Path.home() / ".smartcrack" / "sessions"


def write_session(payload: dict) -> Path:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = SESSION_DIR / f"session_{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def read_sessions(limit: int | None = None) -> list[dict]:
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("session_*.json"), reverse=True)
    if limit:
        files = files[:limit]
    sessions = []
    for f in files:
        try:
            sessions.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sessions


def get_latest_session() -> dict | None:
    sessions = read_sessions(limit=1)
    return sessions[0] if sessions else None
