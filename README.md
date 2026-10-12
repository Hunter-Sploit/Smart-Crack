# SmartCrack

SmartCrack identifies password hash types and gives you ready-to-use `hashcat` and `john` commands. It supports 70+ hash formats and uses confidence scoring to rank candidates.

> **Authorized use only.** Run this tool only on systems you own or have explicit permission to audit.

## Quick Start

```bash
# Clone and install
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure default wordlist (one-time)
python -m smartcrack config --wordlist /path/to/rockyou.txt

# 1. Identify hash type - shows all candidates with commands
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# 2. Crack using auto-detected mode from identification
python -m smartcrack crack --toolname hashcat --wordlist rockyou.txt hash.txt
python -m smartcrack crack --toolname john --wordlist rockyou.txt hash.txt
```

## Features

- **Hash identification** - 70+ hash types with confidence scoring, hashcat mode, and john format
- **Ready-to-run commands** - Copy/paste the exact `hashcat` or `john` command for each candidate
- **Manual workflow** - Identify first, then crack with explicit tool choice (`--toolname hashcat|john`)
- **Auto-detection** - Crack command infers mode/format from identification, with overrides available
- **Persistent config** - Default wordlist saved to `~/.smartcrack/config.json`
- **Session logging** - Full audit trail in `~/.smartcrack/sessions/`
- **Safe subprocess handling** - No shell injection, argument-list execution
- **Clean CLI** - Built with Typer and Rich

## Supported Hash Types (70+)

| Type | Hashcat Mode | John Format |
|------|--------------|-------------|
| MD5 | 0 | raw-md5 |
| SHA1 | 100 | raw-sha1 |
| SHA256 | 1400 | raw-sha256 |
| SHA512 | 1700 | raw-sha512 |
| bcrypt | 3200 | bcrypt |
| NTLM | 1000 | nt |
| NTLMv2 | 5600 | netntlmv2 |
| sha512crypt | 1800 | sha512crypt |
| sha256crypt | 7400 | sha256crypt |
| md5crypt | 500 | md5crypt |
| MySQL 5.7+ | 7401 | mysql-sha1 |
| Kerberos | 13100 | krb5 |
| WPA-PBKDF2 | 2500 | wpapsk |
| ...and 50+ more | | |

Patterns are defined in `smartcrack/identifiers/patterns.json` - easy to extend.

## Installation

### Prerequisites
- Python 3.9+
- `hashcat` (for GPU cracking)
- `john` + extractors (`pdf2john`, `zip2john`, etc.)

### Setup

```bash
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Ubuntu/Debian
sudo apt-get install hashcat john john-data
```

## Usage

### 1. Identify Hash

```bash
# Single hash
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# Multiple hashes from file
python -m smartcrack identify hashes.txt

# JSON output for scripting
python -m smartcrack identify hash.txt --json

# Custom wordlist for command examples
python -m smartcrack identify hash.txt --wordlist rockyou.txt
```

Output shows a table with all candidates, confidence, hashcat/john modes, and ready-to-copy commands.

### 2. Configure Wordlist

```bash
# Set default
python -m smartcrack config --wordlist /path/to/rockyou.txt

# View current config
python -m smartcrack config --show

# Reset to defaults
python -m smartcrack config --reset
```

### 3. Crack (Manual Workflow)

```bash
# Auto-detect mode from identification, use hashcat
python -m smartcrack crack --toolname hashcat --wordlist rockyou.txt hash.txt

# Auto-detect format from identification, use john
python -m smartcrack crack --toolname john --wordlist rockyou.txt hash.txt

# Override hashcat mode if needed
python -m smartcrack crack --toolname hashcat --hashcat-mode 0 --wordlist rockyou.txt hash.txt

# Override john format
python -m smartcrack crack --toolname john --john-format raw-md5 --wordlist rockyou.txt hash.txt

# Use saved wordlist
python -m smartcrack crack --toolname hashcat hash.txt

# Brute-force mask attack (hashcat only)
python -m smartcrack crack --toolname hashcat --mask '?a?a?a?a?a?a' hash.txt

# Use rules file (john only)
python -m smartcrack crack --toolname john --rules /path/to/rules.txt --wordlist rockyou.txt hash.txt
```

| Option | Required | Description |
|--------|----------|-------------|
| `--toolname`, `-t` | Yes | `hashcat` or `john` |
| `--wordlist`, `-w` | Yes* | Wordlist path (uses saved default if omitted) |
| `--hashcat-mode`, `-m` | No | Override auto-detected hashcat mode |
| `--john-format`, `-f` | No | Override auto-detected john format |
| `--mask` | No | Hashcat mask for brute-force |
| `--rules` | No | Rules file path (john only) |

*Required unless `--mask` is used.

## Architecture

```
smartcrack/
├── cli.py                      # Typer + Rich CLI (identify, config, crack)
├── models.py                   # Shared dataclasses
├── __main__.py                 # Entry point
├── config/
│   ├── settings.py            # Pydantic Settings
│   ├── legacy.py              # JSON migration
│   └── store.py               # Compatibility wrappers
├── detectors/
│   └── input_detector.py      # Magic bytes + prefix detection
├── extractors/
│   └── john_extractors.py     # Hash extraction via john tools
├── identifiers/
│   ├── hash_identifier.py     # Pattern-based identification
│   └── patterns.json          # 70+ regex patterns with metadata
├── sessions/
│   └── store.py               # Session logging (JSONL)
├── utils/
│   └── subprocess_safe.py     # Secure subprocess handling
└── tests/
    ├── test_identifier.py
    └── test_cli.py
```

Data flow:
```
User Input → Identify → [shows candidates + commands]
                     ↓
               Crack (manual)
                     ↓
          Internal identify → Auto-detect mode/format
                     ↓
          Build command → Execute hashcat/john
                     ↓
          Log session → Stream output
```

## Testing

```bash
# All tests
python -m pytest tests/ -v

# Identifier tests
python -m pytest tests/test_identifier.py -v

# Config/CLI tests
python -m pytest tests/test_cli.py -v

# Type checking
python -m mypy smartcrack

# Linting
python -m ruff check smartcrack
```

Test files included:
- `example_hashes.txt` - Sample hashes (MD5, SHA1, SHA256, bcrypt, NTLM, etc.)
- `wordlist_sample.txt` - 50 common passwords for testing

## Configuration

Stored at `~/.smartcrack/config.json`:

```json
{
  "default_wordlist": "/path/to/rockyou.txt",
  "wordlists": ["/path/to/rockyou.txt", "/other/list.txt"],
  "preferred_tool": null,
  "timeout_seconds": 3600,
  "session_dir": "~/.smartcrack/sessions"
}
```

Environment variables (prefix `SMARTCRACK_`):
```bash
export SMARTCRACK_DEFAULT_WORDLIST=/path/to/wordlist.txt
export SMARTCRACK_TIMEOUT_SECONDS=7200
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `hashcat: command not found` | Install: `sudo apt-get install hashcat` |
| `john: command not found` | Install: `sudo apt-get install john` |
| Hash not identified | Check format; try `--json` for raw output |
| Crack finds nothing | Larger wordlist or different mask |
| Permission denied on config | Ensure `~/.smartcrack/` exists |
| Oracle hash not detected | Must be 48-60 hex chars |

## Roadmap / Limitations

**Current limits:**
- Basic extractor coverage (PDF, ZIP, RAR, 7z, Office, SSH)
- Pattern-based identification only (no ML)
- No distributed cracking
- No resume for interrupted cracks (session logging only)

**Planned:**
- Resume from session
- Progress reporting for long cracks
- Plugin system for custom extractors/identifiers
- More archive format support

## Contributing

Contributions welcome:

1. **New Extractors** - More archive formats
2. **Hash Types** - Extend `patterns.json`
3. **Performance** - Optimize for large hash lists
4. **Documentation** - Examples and guides
5. **Tests** - Integration tests with mocked backends

## License

MIT - See LICENSE file.

## Legal Disclaimer

This tool is for **authorized security testing and education only**. Unauthorized access to computer systems is illegal. You are responsible for:
- Obtaining proper authorization
- Complying with applicable laws
- Using this tool ethically
- Respecting privacy and security

The developers assume no liability for misuse or damage.

## Support

- Open a GitHub Issue
- Check existing issues first
- Provide detailed error messages and reproduction steps

---

**SmartCrack** - Identify hashes, crack responsibly.