"""Legacy PDF dictionary cracker logic retained and modernized from original script."""

from __future__ import annotations

from pathlib import Path

import pikepdf


def crack_pdf_with_wordlist(pdf_path: Path, wordlist_path: Path) -> str | None:
    for password in wordlist_path.read_text(errors="ignore").splitlines():
        candidate = password.strip()
        if not candidate:
            continue
        try:
            with pikepdf.open(str(pdf_path), password=candidate):
                return candidate
        except pikepdf.PasswordError:
            continue
    return None
