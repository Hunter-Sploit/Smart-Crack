from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from smartcrack.models import HashCandidate


def load_patterns() -> list[dict[str, Any]]:
    patterns_path = Path(__file__).parent / "patterns.json"
    with patterns_path.open("r") as f:
        return json.load(f)


PATTERNS = load_patterns()


def _calculate_confidence(pattern: dict[str, Any], text: str) -> float:
    base = pattern.get("priority", 50) / 100.0
    metadata = pattern.get("metadata", {})

    if metadata.get("type") == "crypt":
        return min(base + 0.1, 0.99)
    if metadata.get("type") in {"archive", "kerberos", "ldap", "database", "app", "network", "legacy"}:
        return min(base + 0.05, 0.95)
    if metadata.get("type") == "salted":
        return min(base + 0.05, 0.95)
    if metadata.get("type") == "raw":
        ctx = metadata.get("context", "generic")
        if ctx == "windows" and "NTLM" in pattern["name"]:
            return min(base + 0.05, 0.95)
        return base

    return base


def _build_commands(candidate: HashCandidate, wordlist: str = "wordlist.txt") -> dict[str, str]:
    commands = {}
    if candidate.hashcat_mode is not None:
        commands["hashcat"] = f"hashcat -m {candidate.hashcat_mode} -a 0 hash.txt {wordlist}"
    if candidate.john_format is not None:
        commands["john"] = f"john --format={candidate.john_format} --wordlist={wordlist} hash.txt"
    return commands


def identify_hash(text: str, wordlist: str = "wordlist.txt") -> list[HashCandidate]:
    text = text.strip()
    candidates: list[HashCandidate] = []

    for pattern in PATTERNS:
        if re.search(pattern["pattern"], text):
            confidence = _calculate_confidence(pattern, text)
            candidate = HashCandidate(
                name=pattern["name"],
                confidence=confidence,
                hashcat_mode=pattern.get("hashcat_mode"),
                john_format=pattern.get("john_format"),
                notes=f"pattern match (priority: {pattern.get('priority', 50)})"
            )
            candidates.append(candidate)

    if text.startswith("$krb5"):
        candidates.append(HashCandidate(
            name="Kerberos",
            confidence=0.85,
            hashcat_mode=13100,
            john_format="krb5",
            notes="prefix heuristic"
        ))

    if text.count(".") == 2 and len(text.split(".")) == 3:
        parts = text.split(".")
        if all(re.match(r"^[A-Za-z0-9_-]+$", p) for p in parts):
            candidates.append(HashCandidate(
                name="JWT",
                confidence=0.65,
                hashcat_mode=None,
                john_format=None,
                notes="token shape"
            ))

    if not candidates and len(text) in {32, 40, 64, 128} and all(c in "0123456789abcdefABCDEF" for c in text):
        candidates.append(HashCandidate(
            name="Unknown Hex",
            confidence=0.40,
            hashcat_mode=None,
            john_format=None,
            notes="hex digest heuristic"
        ))

    seen = set()
    unique = []
    for c in sorted(candidates, key=lambda x: x.confidence, reverse=True):
        key = (c.name, c.hashcat_mode, c.john_format)
        if key not in seen:
            seen.add(key)
            c.commands = _build_commands(c, wordlist)
            unique.append(c)

    return unique


def get_identification_table_data(candidates: list[HashCandidate]) -> list[dict[str, str]]:
    rows = []
    for c in candidates:
        hc = str(c.hashcat_mode) if c.hashcat_mode is not None else "-"
        jf = c.john_format or "-"
        hc_cmd = c.commands.get("hashcat", "-") if hasattr(c, "commands") else "-"
        j_cmd = c.commands.get("john", "-") if hasattr(c, "commands") else "-"
        rows.append({
            "candidate": c.name,
            "confidence": f"{c.confidence:.0%}",
            "hashcat_mode": hc,
            "john_format": jf,
            "hashcat_cmd": hc_cmd,
            "john_cmd": j_cmd,
            "notes": c.notes
        })
    return rows