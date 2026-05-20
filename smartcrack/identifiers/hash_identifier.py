from __future__ import annotations

import re

from smartcrack.models import HashCandidate


PATTERNS: list[tuple[str, str, int | None, str | None]] = [
    (r"^[a-fA-F0-9]{32}$", "MD5", 0, "raw-md5"),
    (r"^[a-fA-F0-9]{40}$", "SHA1", 100, "raw-sha1"),
    (r"^[a-fA-F0-9]{64}$", "SHA256", 1400, "raw-sha256"),
    (r"^\$2[aby]\$\d{2}\$.{53}$", "bcrypt", 3200, "bcrypt"),
    (r"^[a-fA-F0-9]{32}:[A-Fa-f0-9]{32}$", "NTLMv2", 5600, "netntlmv2"),
    (r"^\$pdf\$", "PDF", 10400, "pdf"),
    (r"^\$zip2\$", "ZIP", 13600, "zip"),
]


def identify_hash(text: str) -> list[HashCandidate]:
    text = text.strip()
    candidates: list[HashCandidate] = []
    for pattern, name, mode, john_fmt in PATTERNS:
        if re.search(pattern, text):
            candidates.append(HashCandidate(name=name, confidence=0.95, hashcat_mode=mode, john_format=john_fmt, notes="pattern match"))

    if text.startswith("$krb5"):
        candidates.append(HashCandidate(name="Kerberos", confidence=0.85, hashcat_mode=13100, john_format="krb5", notes="prefix heuristic"))

    if text.count(".") == 2 and len(text.split(".")) == 3:
        candidates.append(HashCandidate(name="JWT", confidence=0.65, hashcat_mode=None, john_format=None, notes="token shape"))

    return sorted(candidates, key=lambda x: x.confidence, reverse=True)
