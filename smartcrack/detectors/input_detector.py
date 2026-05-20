from __future__ import annotations

from pathlib import Path

from smartcrack.models import DetectionResult


MAGIC_SIGNATURES: dict[bytes, str] = {
    b"%PDF": "pdf",
    b"PK\x03\x04": "zip",
    b"Rar!\x1a\x07\x00": "rar",
    b"7z\xbc\xaf\x27\x1c": "7z",
}


RAW_HASH_PREFIX_HINTS = {
    "$2a$": "bcrypt",
    "$2b$": "bcrypt",
    "$6$": "sha512crypt",
    "$5$": "sha256crypt",
    "$1$": "md5crypt",
    "$pdf$": "pdf-hash",
    "$zip2$": "zip-hash",
}


def detect_input(target: str) -> DetectionResult:
    p = Path(target)
    if p.exists() and p.is_file():
        data = p.read_bytes()[:16]
        for sig, kind in MAGIC_SIGNATURES.items():
            if data.startswith(sig):
                return DetectionResult(input_path=p, kind=kind, confidence=0.98, reasons=[f"magic bytes matched {kind}"])
        content_sample = p.read_text(errors="ignore")[:5000]
        if ":" in content_sample and "$" in content_sample:
            return DetectionResult(input_path=p, kind="hash_dump", confidence=0.70, reasons=["text file resembles hash dump"])
        return DetectionResult(input_path=p, kind="file", confidence=0.40, reasons=["generic file"])

    for prefix, kind in RAW_HASH_PREFIX_HINTS.items():
        if target.startswith(prefix):
            return DetectionResult(input_path=None, kind="raw_hash", confidence=0.90, reasons=[f"prefix matched {kind}"])

    if len(target) in {32, 40, 64} and all(c in "0123456789abcdefABCDEF" for c in target):
        return DetectionResult(input_path=None, kind="raw_hash", confidence=0.80, reasons=["hex digest heuristic"])

    return DetectionResult(input_path=None, kind="unknown", confidence=0.10, reasons=["no heuristic matched"])
