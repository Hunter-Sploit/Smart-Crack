from __future__ import annotations

from pathlib import Path

from smartcrack.models import DetectionResult

MAGIC_SIGNATURES: dict[bytes, str] = {
    b"%PDF": "pdf",
    b"PK\x03\x04": "zip",
    b"Rar!\x1a\x07\x00": "rar",
    b"7z\xbc\xaf\x27\x1c": "7z",
    # OLE Compound Document (old Office .doc, .xls, .ppt)
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "office",
    # OpenSSH private key (new format)
    b"-----BEGIN OPENSSH PRIVATE KEY-----": "ssh",
    # PEM format RSA/DSA/EC private keys
    b"-----BEGIN RSA PRIVATE KEY-----": "ssh",
    b"-----BEGIN DSA PRIVATE KEY-----": "ssh",
    b"-----BEGIN EC PRIVATE KEY-----": "ssh",
    b"-----BEGIN PRIVATE KEY-----": "ssh",
}


RAW_HASH_PREFIX_HINTS = {
    "$2a$": "bcrypt",
    "$2b$": "bcrypt",
    "$2y$": "bcrypt",
    "$6$": "sha512crypt",
    "$5$": "sha256crypt",
    "$1$": "md5crypt",
    "$pdf$": "pdf-hash",
    "$zip2$": "zip-hash",
    "$rar$": "rar-hash",
    "$7z$": "7z-hash",
    "$office$": "office-hash",
    "$oldoffice$": "office-hash",
    "$krb5": "kerberos",
    "$krb5asrep$": "kerberos-asrep",
    "$krb5tgs$": "kerberos-tgs",
    "$apr1$": "apache-md5",
    "$P$": "phpass",
    "$H$": "phpass",
}


def detect_input(target: str) -> DetectionResult:
    p = Path(target)
    if p.exists() and p.is_file():
        # Read enough bytes to cover all magic signatures (SSH keys are ~36 bytes)
        data = p.read_bytes()[:64]
        for sig, kind in MAGIC_SIGNATURES.items():
            if data.startswith(sig):
                return DetectionResult(input_path=p, kind=kind, confidence=0.98, reasons=[f"magic bytes matched {kind}"])

        # Check for newer Office formats (.docx, .xlsx, .pptx) - these are ZIP-based
        if data.startswith(b"PK\x03\x04"):
            # Could be a modern Office file, check content
            try:
                content = p.read_bytes()[:5000]
                if b"[Content_Types].xml" in content and (b"word/" in content or b"xl/" in content or b"ppt/" in content):
                    return DetectionResult(input_path=p, kind="office", confidence=0.90, reasons=["ZIP structure matches Office Open XML"])
            except (OSError, UnicodeDecodeError):
                pass

        # Check for hash dump files
        content_sample = p.read_text(errors="ignore")[:5000]
        if ":" in content_sample and "$" in content_sample:
            return DetectionResult(input_path=p, kind="hash_dump", confidence=0.70, reasons=["text file resembles hash dump"])

        # Check for SSH private key in text form
        if content_sample.lstrip().startswith("-----BEGIN") and "PRIVATE KEY" in content_sample:
            return DetectionResult(input_path=p, kind="ssh", confidence=0.95, reasons=["PEM private key detected"])

        return DetectionResult(input_path=p, kind="file", confidence=0.40, reasons=["generic file"])

    # Raw string input - check hash prefixes
    for prefix, kind in RAW_HASH_PREFIX_HINTS.items():
        if target.startswith(prefix):
            return DetectionResult(input_path=None, kind="raw_hash", confidence=0.90, reasons=[f"prefix matched {kind}"])

    # Check for PEM private key in raw string
    if target.lstrip().startswith("-----BEGIN") and "PRIVATE KEY" in target:
        return DetectionResult(input_path=None, kind="raw_hash", confidence=0.90, reasons=["PEM private key detected"])

    # Hex digest heuristic
    if len(target) in {32, 40, 64, 128} and all(c in "0123456789abcdefABCDEF" for c in target):
        return DetectionResult(input_path=None, kind="raw_hash", confidence=0.80, reasons=["hex digest heuristic"])

    # JWT token heuristic
    if target.count(".") == 2 and len(target.split(".")) == 3:
        parts = target.split(".")
        if all(c.isalnum() or c in "-_" for p in parts for c in p):
            return DetectionResult(input_path=None, kind="raw_hash", confidence=0.65, reasons=["JWT token shape"])

    return DetectionResult(input_path=None, kind="unknown", confidence=0.10, reasons=["no heuristic matched"])
