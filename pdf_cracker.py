"""Backward-compatible launcher for legacy PDF cracking workflow.

Use `python -m smartcrack.cli crack <file.pdf> --wordlist <wordlist>` for the full framework.
"""

from __future__ import annotations

from pathlib import Path

from smartcrack.pdf_legacy import crack_pdf_with_wordlist


if __name__ == "__main__":
    pdf = Path("remote.pdf")
    wordlist = Path("wordlist.txt")
    password = crack_pdf_with_wordlist(pdf, wordlist)
    if password:
        print(f"Password Found: {password}")
    else:
        print("Password not found in wordlist")
