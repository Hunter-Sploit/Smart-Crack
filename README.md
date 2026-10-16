# SmartCrack

SmartCrack identifies password hash types and gives you ready-to-use `hashcat` and `john` commands. It supports 70+ hash formats and uses confidence scoring to rank candidates.

> **Authorized use only.** Run this tool only on systems you own or have explicit permission to audit.

## Quick Start

> 📘 For a full step-by-step walkthrough, see the [Getting Started Guide](GETTING_STARTED.md).

```bash
# 1. Clone repository
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack

# 2. Automated Install (Linux / macOS)
./install.sh
source .venv/bin/activate

# Windows: run install.bat or .\install.ps1

# 3. Identify a hash (single hash, file, or credential dump)
smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# 4. Crack automatically (auto-selects tool and wordlist)
smartcrack crack example_hashes.txt
```

*Or run directly without activating the virtual environment:*
```bash
./run.sh identify example_hashes.txt
./run.sh crack example_hashes.txt
```

## Features

- **Hash identification (80+ types)** - MD5, SHA1, SHA256, bcrypt, Argon2, NTLM, sha512crypt, Kerberos, Cisco, and more
- **Structured format extraction** - Automatically parses Linux `/etc/shadow`, Windows pwdump/SAM dumps, and `user:hash` formats
- **Ready-to-run commands** - Copy/paste exact `hashcat` and `john` commands generated for every candidate
- **Zero-friction cracking** - Auto-detects tool (`hashcat` or `john`) and wordlist (`wordlist_sample.txt` or `rockyou.txt`) if omitted
- **Interactive fallback** - Prompts politely if input is omitted rather than erroring out
- **1-Click Installers** - Quick setup scripts (`install.sh`, `install.bat`, `install.ps1`) for Linux, macOS, and Windows
- **Direct CLI entrypoint** - Run `smartcrack` anywhere inside the environment
- **Safe execution** - Non-shell subprocess execution preventing injection vulnerabilities
- **Persistent configuration** - Default wordlist and settings saved to `~/.smartcrack/config.json`

## Supported Hash Types (80+)

| Type | Hashcat Mode | John Format |
|------|--------------|-------------|
| MD5 | 0 | raw-md5 |
| SHA1 | 100 | raw-sha1 |
| SHA256 | 1400 | raw-sha256 |
| SHA512 | 1700 | raw-sha512 |
| SHA-384 / SHA-224 | 10800 / 1400 | raw-sha384 / raw-sha224 |
| bcrypt | 3200 | bcrypt |
| Argon2 (id/i/d) | 7300 | argon2 |
| NTLM / NTLMv2 | 1000 / 5600 | nt / netntlmv2 |
| sha512crypt | 1800 | sha512crypt |
| sha256crypt | 7400 | sha256crypt |
| md5crypt | 500 | md5crypt |
| MySQL 5.7+ | 7401 | mysql-sha1 |
| Kerberos (AS-REP / TGS) | 18200 / 13100 | krb5asrep / krb5 |
| Cisco Type 8 / 9 | 9200 / 9300 | cisco8 / cisco9 |
| WPA-PBKDF2 | 2500 | wpapsk |
| ...and 60+ more | | |

Patterns are defined in `smartcrack/identifiers/patterns.json` - easy to extend.

## Installation

### 1-Click Automated Setup
- **Linux / macOS**:
  ```bash
  ./install.sh
  source .venv/bin/activate
  ```
- **Windows**:
  ```cmd
  install.bat
  .venv\Scripts\activate
  ```

### Manual Setup
```bash
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Ubuntu/Debian Cracking Backends
sudo apt-get install hashcat john john-data
```

## Usage

### 1. Identify Hashes

```bash
# Single hash (wrap in quotes if it contains '$')
smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# Credential dump line (/etc/shadow, pwdump, or user:hash)
smartcrack identify 'root:$6$rounds=5000$salt$hash:18000:0:99999:7:::'
smartcrack identify 'admin:5f4dcc3b5aa765d61d8327deb882cf99'

# Multiple hashes from file
smartcrack identify hashes.txt

# JSON output for scripting
smartcrack identify hashes.txt --json

# Interactive mode (prompts for hash)
smartcrack identify
```

### 2. Crack Hashes

```bash
# Automatic (infers format, detects installed tool, uses default or detected wordlist)
smartcrack crack example_hashes.txt

# Explicit tool choice
smartcrack crack -t hashcat -w wordlist_sample.txt example_hashes.txt
smartcrack crack -t john -w wordlist_sample.txt example_hashes.txt

# Brute-force mask attack (Hashcat)
smartcrack crack -m 0 --mask '?d?d?d?d' hash.txt
```

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