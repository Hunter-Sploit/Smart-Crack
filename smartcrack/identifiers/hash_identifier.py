from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from smartcrack.models import HashCandidate


def load_patterns() -> list[dict[str, Any]]:
    patterns_path = Path(__file__).parent / "patterns.json"
    with patterns_path.open("r") as f:
        return cast(list[dict[str, Any]], json.load(f))


PATTERNS = load_patterns()


def clean_input_string(raw: str) -> str:
    """Strip whitespace, inline comments, and quotes from user/file input."""
    s = raw.strip()
    # Strip inline comment like " <hash> # comment" or " <hash> // comment"
    if " #" in s:
        s = s.split(" #", 1)[0].strip()
    elif " //" in s:
        s = s.split(" //", 1)[0].strip()
    # Strip quotes if enclosed
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return s


def extract_hash_from_credential_string(raw: str) -> tuple[str, str | None, str | None]:
    """
    Extract (clean_hash, username, format_hint) from common credential/dump formats.
    Returns (raw, None, None) if no structured format is detected.
    """
    s = clean_input_string(raw)

    # 1. /etc/shadow format: user:$id$...:...
    # e.g., root:$6$rounds=5000$salt$hash:18000:0:99999:7:::
    if s.count(":") >= 2 and "$" in s:
        parts = s.split(":")
        user = parts[0]
        hash_candidate = parts[1]
        if hash_candidate.startswith("$"):
            return hash_candidate, user, "/etc/shadow"

    # 2. Windows pwdump / samdump format: user:uid:lm:ntlm:::
    # e.g., Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
    if s.count(":") >= 3:
        parts = s.split(":")
        user = parts[0]
        if len(parts) >= 4 and len(parts[3]) == 32 and all(c in "0123456789abcdefABCDEF" for c in parts[3]):
            return parts[3], user, "pwdump (NTLM)"
        if len(parts) >= 3 and len(parts[2]) == 32 and all(c in "0123456789abcdefABCDEF" for c in parts[2]):
            return parts[2], user, "pwdump (LM)"

    # 3. htpasswd / user:hash format: username:hash
    if ":" in s and not s.startswith("$"):
        user, rest = s.split(":", 1)
        # Avoid treating salted hashes like 32hex:salt as user:hash
        # If rest starts with crypt prefix ($2b$, $6$, $apr1$, $1$, etc.) or is standard hex length
        if rest.startswith("$") or (len(rest) in {32, 40, 64, 128} and all(c in "0123456789abcdefABCDEF" for c in rest)):
            return rest, user, "user:hash"

    return s, None, None


def _calculate_confidence(pattern: dict[str, Any], text: str) -> float:
    base: float = float(pattern.get("priority", 50)) / 100.0
    metadata = pattern.get("metadata", {}) or {}
    mtype: str | None = metadata.get("type")
    context: str = metadata.get("context", "generic") or "generic"

    if mtype == "crypt":
        return float(min(base + 0.1, 0.99))
    if mtype in {"archive", "kerberos", "ldap", "database", "app", "network", "legacy"}:
        return float(min(base + 0.05, 0.95))
    if mtype == "salted":
        return float(min(base + 0.05, 0.95))
    if mtype == "raw":
        if context == "windows" and "NTLM" in pattern["name"]:
            return float(min(base + 0.05, 0.95))
        return base

    return base


def _build_commands(candidate: HashCandidate, wordlist: str = "wordlist.txt") -> dict[str, str]:
    commands: dict[str, str] = {}
    if candidate.hashcat_mode is not None:
        commands["hashcat"] = f"hashcat -m {candidate.hashcat_mode} -a 0 hash.txt {wordlist}"
    if candidate.john_format is not None:
        commands["john"] = f"john --format={candidate.john_format} --wordlist={wordlist} hash.txt"
    return commands


def _match_patterns(text: str, extra_note: str = "") -> list[HashCandidate]:
    candidates: list[HashCandidate] = []

    for pattern in PATTERNS:
        if re.search(pattern["pattern"], text):
            confidence = _calculate_confidence(pattern, text)
            note = f"pattern match (priority: {pattern.get('priority', 50)})"
            if extra_note:
                note += f" {extra_note}"
            candidate = HashCandidate(
                name=pattern["name"],
                confidence=confidence,
                hashcat_mode=pattern.get("hashcat_mode"),
                john_format=pattern.get("john_format"),
                notes=note,
            )
            candidates.append(candidate)

    if text.startswith("$krb5"):
        note = "prefix heuristic"
        if extra_note:
            note += f" {extra_note}"
        candidates.append(HashCandidate(
            name="Kerberos",
            confidence=0.85,
            hashcat_mode=13100,
            john_format="krb5",
            notes=note,
        ))

    if text.startswith(("$argon2id$", "$argon2i$", "$argon2d$")):
        note = "argon2 prefix heuristic"
        if extra_note:
            note += f" {extra_note}"
        candidates.append(HashCandidate(
            name="Argon2",
            confidence=0.99,
            hashcat_mode=7300,
            john_format="argon2",
            notes=note,
        ))

    if text.count(".") == 2 and len(text.split(".")) == 3:
        parts = text.split(".")
        if all(re.match(r"^[A-Za-z0-9_-]+$", p) for p in parts):
            note = "token shape"
            if extra_note:
                note += f" {extra_note}"
            candidates.append(HashCandidate(
                name="JWT",
                confidence=0.65,
                hashcat_mode=None,
                john_format=None,
                notes=note,
            ))

    if not candidates and len(text) in {32, 40, 64, 128} and all(c in "0123456789abcdefABCDEF" for c in text):
        note = "hex digest heuristic"
        if extra_note:
            note += f" {extra_note}"
        candidates.append(HashCandidate(
            name="Unknown Hex",
            confidence=0.40,
            hashcat_mode=None,
            john_format=None,
            notes=note,
        ))

    return candidates


def identify_hash(text: str, wordlist: str = "wordlist.txt") -> list[HashCandidate]:
    clean_text = clean_input_string(text)
    if not clean_text:
        return []

    # 1. First attempt direct match
    candidates = _match_patterns(clean_text)

    # 2. If no match or only generic Unknown Hex, try extracting from dump/shadow/user:hash format
    if not candidates or (len(candidates) == 1 and candidates[0].name == "Unknown Hex"):
        extracted_hash, user, fmt_hint = extract_hash_from_credential_string(clean_text)
        if extracted_hash != clean_text and fmt_hint:
            user_info = f", user: {user}" if user else ""
            extracted_candidates = _match_patterns(
                extracted_hash,
                extra_note=f"(extracted from {fmt_hint}{user_info})"
            )
            if extracted_candidates:
                candidates = extracted_candidates

    seen: set[tuple[str, int | None, str | None]] = set()
    unique: list[HashCandidate] = []
    for c in sorted(candidates, key=lambda x: x.confidence, reverse=True):
        key = (c.name, c.hashcat_mode, c.john_format)
        if key not in seen:
            seen.add(key)
            c.commands = _build_commands(c, wordlist)
            unique.append(c)

    return unique


def get_identification_table_data(candidates: list[HashCandidate]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
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