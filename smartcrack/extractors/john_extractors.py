from __future__ import annotations

from pathlib import Path

from smartcrack.models import ExtractedHash
from smartcrack.utils.subprocess_safe import run_command, which

EXTRACTOR_MAP = {

    "pdf": "pdf2john",


    "zip": "zip2john",


    "rar": "rar2john",


    "7z": "7z2john.pl",


    "office": "office2john",


    "ssh": "ssh2john",

}

def extract_hash(path: Path, kind: str) -> list[ExtractedHash]:
    tool = EXTRACTOR_MAP.get(kind)
    if not tool:
        return []
    if not which(tool):
        return []
    result = run_command([tool, str(path)])
    if result.code != 0 or not result.stdout.strip():
        return []

    lines = [x.strip() for x in result.stdout.splitlines() if x.strip()]
    out: list[ExtractedHash] = []
    for line in lines:
        if line.startswith("$"):
            payload = line
        elif ":" in line:
            parts = line.split(":", 1)
            payload = parts[1] if len(parts) > 1 else line
        else:
            payload = line

        out.append(ExtractedHash(source=kind, raw_hash=payload))
    return out
