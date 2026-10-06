from __future__ import annotations

import re

from smartcrack.models import HashCandidate


# (pattern, name, hashcat_mode, john_format)
# Ordered by specificity - prefix-based formats first, then length-based.
# For ambiguous lengths (e.g. MD5 vs NTLM), the most common interpretation
# comes first so it becomes the top candidate.
PATTERNS: list[tuple[str, str, int | None, str | None]] = [
    # --- Crypt formats (prefix-based, most specific) ---
    (r"^\$6\$", "sha512crypt", 1800, "sha512crypt"),
    (r"^\$5\$", "sha256crypt", 7400, "sha256crypt"),
    (r"^\$1\$", "md5crypt", 500, "md5crypt"),
    (r"^\$apr1\$[A-Za-z0-9./]{8}\$[A-Za-z0-9./]{22}$", "Apache MD5 (apr1)", 1600, "apache-md5"),
    (r"^\$P\$[A-Za-z0-9./]{31}$", "phpass", 400, "phpass"),
    (r"^\$H\$[A-Za-z0-9./]{31}$", "phpass (portable)", 400, "phpass"),
    (r"^\$2[aby]\$\d{2}\$.{53}$", "bcrypt", 3200, "bcrypt"),
    (r"^\$WPA\$", "WPA-PBKDF2", 2500, "wpapsk"),
    (r"^\$SHA\$[0-9]+\$[A-Za-z0-9./]{8}\$[A-Za-z0-9./]{43}$", "SHA (Sun)", 3300, "sun-md5"),
    (r"^_[a-zA-Z0-9./]{20}$", "BSDi Crypt", 12400, "bsdi"),
    (r"^[a-zA-Z0-9./]{13}$", "DES crypt", 1500, "descrypt"),

    # --- Archive / encryption hashes ---
    (r"^\$pdf\$", "PDF", 10400, "pdf"),
    (r"^\$zip2\$", "ZIP", 13600, "zip"),
    (r"^\$rar\$", "RAR", 13000, "rar"),
    (r"^\$7z\$", "7-Zip", 11600, "7z"),
    (r"^\$office\$", "MS Office", 9400, "office"),
    (r"^\$oldoffice\$", "MS Office (old)", 9700, "oldoffice"),

    # --- Kerberos ---
    (r"^\$krb5", "Kerberos", 13100, "krb5"),

    # --- LDAP ---
    (r"^\{SHA\}[A-Za-z0-9+/]+={0,2}$", "LDAP SHA1", 101, "nsldap"),
    (r"^\{SSHA\}[A-Za-z0-9+/]+={0,2}$", "LDAP SSHA1", 111, "nsldaps"),
    (r"^\{SSHA256\}[A-Za-z0-9+/]+={0,2}$", "LDAP SSHA256", 1411, "ldap-sha256"),
    (r"^\{SSHA512\}[A-Za-z0-9+/]+={0,2}$", "LDAP SSHA512", 1711, "ldap-sha512"),

    # --- Database ---
    (r"^\*[A-F0-9]{40}$", "MySQL 5.7+", 7401, "mysql-sha1"),
    (r"^0x0100[a-fA-F0-9]{82}$", "MSSQL 2000", 131, "mssql"),
    (r"^0x0200[a-fA-F0-9]{82}$", "MSSQL 2012+", 1731, "mssql12"),
    (r"^[A-F0-9]{60,}$", "Oracle 10g/11g", 3100, "oracle11"),

    # --- Application-specific ---
    (r"^sha1\$[a-fA-F0-9]{12}\$[a-fA-F0-9]{40}$", "Django SHA1", 124, "django"),
    (r"^[A-Fa-f0-9]{16}$", "LM", 3000, "lm"),
    (r"^[A-Za-z0-9+/]+={0,2}:[A-Fa-f0-9]{8}$", "Juniper NetScreen", 22, "juniper"),
    (r"^3u\+[A-Za-z0-9+/]+={0,2}$", "Juniper IVE", 501, "juniper-ive"),
    (r"^[A-Fa-f0-9]{16}:[A-Fa-f0-9]{16}$", "Cisco PIX/ASA", 2400, "cisco-pix"),

    # --- Raw hashes (length-based, most common first) ---
    (r"^[a-fA-F0-9]{32}$", "MD5", 0, "raw-md5"),
    (r"^[a-fA-F0-9]{40}$", "SHA1", 100, "raw-sha1"),
    (r"^[a-fA-F0-9]{64}$", "SHA256", 1400, "raw-sha256"),
    (r"^[a-fA-F0-9]{128}$", "SHA512", 1700, "raw-sha512"),

    # --- Ambiguous alternatives (same length as above, lower priority) ---
    (r"^[a-fA-F0-9]{32}$", "NTLM", 1000, "nt"),
    (r"^[a-fA-F0-9]{40}$", "RIPEMD-160", 6000, "ripemd160"),
    (r"^[a-fA-F0-9]{96}$", "Whirlpool", 6100, "whirlpool"),
    (r"^[a-fA-F0-9]{64}$", "GOST R 34.11-94", 6900, "gost"),
    (r"^[a-fA-F0-9]{56}$", "SHA3-224", 17300, "sha3-224"),
    (r"^[a-fA-F0-9]{64}$", "SHA3-256", 17400, "sha3-256"),
    (r"^[a-fA-F0-9]{96}$", "SHA3-384", 17500, "sha3-384"),
    (r"^[a-fA-F0-9]{128}$", "SHA3-512", 17600, "sha3-512"),

    # --- Salted / concatenated formats ---
    (r"^[a-fA-F0-9]{32}:[A-Fa-f0-9]{32}$", "NTLMv2", 5600, "netntlmv2"),
    (r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{1,}$", "MD5 (salted)", 10, "md5-salted"),
    (r"^[a-fA-F0-9]{40}:[a-fA-F0-9]{1,}$", "SHA1 (salted)", 110, "sha1-salted"),
    (r"^[a-fA-F0-9]{64}:[a-fA-F0-9]{1,}$", "SHA256 (salted)", 1410, "sha256-salted"),
    (r"^[a-fA-F0-9]{128}:[a-fA-F0-9]{1,}$", "SHA512 (salted)", 1710, "sha512-salted"),

    # --- Application-specific salted ---
    (r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{3,}$", "vBulletin", 2611, "vbulletin"),
    (r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{5}$", "IPB/MyBB", 2811, "ipb"),
]


def identify_hash(text: str) -> list[HashCandidate]:
    text = text.strip()
    candidates: list[HashCandidate] = []

    for pattern, name, mode, john_fmt in PATTERNS:
        if re.search(pattern, text):
            candidates.append(HashCandidate(name=name, confidence=0.95, hashcat_mode=mode, john_format=john_fmt, notes="pattern match"))

    # Fallback heuristics for things that don't match patterns cleanly
    if text.startswith("$krb5"):
        candidates.append(HashCandidate(name="Kerberos", confidence=0.85, hashcat_mode=13100, john_format="krb5", notes="prefix heuristic"))

    # JWT tokens - three base64url parts separated by dots
    if text.count(".") == 2 and len(text.split(".")) == 3:
        parts = text.split(".")
        if all(re.match(r"^[A-Za-z0-9_-]+$", p) for p in parts):
            candidates.append(HashCandidate(name="JWT", confidence=0.65, hashcat_mode=None, john_format=None, notes="token shape"))

    # Generic hex fallback - only if nothing else matched
    if not candidates:
        if len(text) in {32, 40, 64, 128} and all(c in "0123456789abcdefABCDEF" for c in text):
            candidates.append(HashCandidate(name="Unknown Hex", confidence=0.40, hashcat_mode=None, john_format=None, notes="hex digest heuristic"))

    return sorted(candidates, key=lambda x: x.confidence, reverse=True)
