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
