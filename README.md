# SmartCrack

SmartCrack evolves the original PDF-only cracker into a modular intelligent cracking framework that automates detection, extraction, identification, and cracking orchestration across Hashcat and John the Ripper.

> Authorized-use only: run this tool only on systems/files you own or are explicitly permitted to audit.

## Architecture

```text
smartcrack/
  cli.py                    # Typer + Rich CLI
  models.py                 # Shared dataclasses
  detectors/input_detector.py
  extractors/john_extractors.py
  identifiers/hash_identifier.py
  crackers/planner.py
  config/store.py
  sessions/store.py
  utils/subprocess_safe.py
  plugins/                  # Extension point
```

## Key Features

- Smart input detection via magic bytes + heuristics (PDF/ZIP/RAR/7z/hash dump/raw hash)
- Automatic extractor routing (`pdf2john`, `zip2john`, `rar2john`, etc.) when available
- Hash identify mode with confidence and backend hints (hashcat mode + john format)
- Backend planner (Hashcat preferred for GPU-ready modes; John fallback)
- Configured wordlist management (`~/.smartcrack/config.json`)
- Session logging (`~/.smartcrack/sessions/*.json`) for resume/forensics/history
- Safe subprocess handling (no shell interpolation, argument lists only)
- Single CLI entrypoint (`python -m smartcrack`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install cracking dependencies separately:
- `hashcat`
- `john` and john helper extractors (`pdf2john`, `zip2john`, etc.)

## Usage

### Configure default wordlist
```bash
python -m smartcrack config --wordlist /path/to/rockyou.txt
```

### Identify hash
```bash
python -m smartcrack identify '$2b$12$abcdefghijklmnopqrstuu5f6rXHfQZfI5XjVd2kB6vhcxRkq'
python -m smartcrack identify hashes.txt
```

### Crack (auto workflow)
```bash
python -m smartcrack crack secret.pdf
python -m smartcrack crack archive.zip --wordlist /path/to/wordlist.txt
python -m smartcrack crack dump.hash --backend john
python -m smartcrack crack '$1c8bfe8f801d79745c4631d09fff36c82' --wordlist /path/to/wl.txt
```

### Hashcat mask override
```bash
python -m smartcrack crack dump.hash --mask '?a?a?a?a?a?a'
```

## Current limitations and next improvements

- Extractor coverage is scaffolded and easy to extend, but not all formats are deeply normalized yet.
- Recommendation engine is basic and should be expanded with probabilistic strategy scoring.
- Distributed cracking/API/dashboard features are intentionally not included in this first generalized baseline.

## Notes

- PDF extraction now requires `pdf2john` to be installed and available in `PATH`.
