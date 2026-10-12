# SmartCrack

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SmartCrack** is a modular password hash identification and cracking tool that identifies hash types with confidence scoring and provides ready-to-use hashcat/john commands. It supports 70+ hash types and integrates with both Hashcat and John the Ripper.

> ⚠️ **Authorized-use only**: Run this tool only on systems/files you own or are explicitly permitted to audit. Unauthorized access to computer systems is illegal.

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure default wordlist
python -m smartcrack config --wordlist /path/to/wordlist.txt

# 1. Identify hash type (shows all candidates with commands)
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# 2. Crack using auto-detected mode from identification
python -m smartcrack crack --toolname hashcat --wordlist wordlist_sample.txt hash.txt
python -m smartcrack crack --toolname john --wordlist wordlist_sample.txt hash.txt
```

---

## ✨ Key Features

- **🔍 Hash Identification**: Identifies 70+ hash types with confidence scoring
  - Displays hashcat mode and john format for each candidate
  - Shows ready-to-copy commands for both tools
  - JSON output for scripting (`--json`)
- **🎯 Manual Crack Workflow**: Identify first, then crack with explicit tool
  - Auto-detects hashcat mode / john format from identification
  - Override with `--hashcat-mode` or `--john-format` if needed
  - Wordlist persists between runs
- **📝 Configuration Management**: Persistent wordlist and preferences
  - `~/.smartcrack/config.json` (Pydantic Settings with env var support)
  - Centralized wordlist management
- **📊 Session Logging**: Complete audit trail
  - `~/.smartcrack/sessions/*.json` for forensics and history
- **🛡️ Safe Subprocess Handling**: No shell injection vulnerabilities
  - Argument list-based execution
- **🎛️ Clean CLI**: Typer + Rich for beautiful, responsive interface

---

## 📋 Supported Hash Types (70+)

| Hash Type | Hashcat Mode | John Format | Example |
|-----------|--------------|-------------|---------|
| MD5 | 0 | raw-md5 | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA1 | 100 | raw-sha1 | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA256 | 1400 | raw-sha256 | `5e884898da28047151d0e56f8dc62927845f5c520a550de58b9c47af9ad8e217` |
| SHA512 | 1700 | raw-sha512 | `...` |
| bcrypt | 3200 | bcrypt | `$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u` |
| NTLM | 1000 | nt | `8846f7eaee8fb117ad06bdd830b7586c` |
| NTLMv2 | 5600 | netntlmv2 | `admin::domain:...` |
| sha512crypt | 1800 | sha512crypt | `$6$...` |
| sha256crypt | 7400 | sha256crypt | `$5$...` |
| md5crypt | 500 | md5crypt | `$1$...` |
| MySQL 5.7+ | 7401 | mysql-sha1 | `*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19` |
| Kerberos | 13100 | krb5 | `$krb5...` |
| WPA-PBKDF2 | 2500 | wpapsk | `$WPA$...` |
| ...and 50+ more | | | |

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- `hashcat` (for GPU-accelerated cracking)
- `john` + extractors like `pdf2john`, `zip2john` (for archive hash extraction)

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install system dependencies (Ubuntu/Debian)
sudo apt-get install hashcat john
sudo apt-get install john-data  # Optional: adds more john modules

# 5. Configure default wordlist
python -m smartcrack config --wordlist /path/to/wordlist.txt
```

---

## 📚 Usage Guide

### 1. Identify Hash Type

```bash
# Single hash - shows all candidates with commands
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# Multiple hashes from file
python -m smartcrack identify hashes.txt

# JSON output for scripting
python -m smartcrack identify hash.txt --json

# Custom wordlist for command examples
python -m smartcrack identify hash.txt --wordlist rockyou.txt
```

**Output Example:**
```
                            Identification Results
+-----------------------------------------------------------------------------+
|           |       | Hashcat   | John      | Hashcat  | John      |          |
| Candidate | Conf. | Mode      | Format    | Command  | Command   | Notes    |
|-----------+-------+-----------+-----------+----------+-----------+----------|
| bcrypt    | 99%   | 3200      | bcrypt    | hashcat  | john      | pattern  |
|           |       |           |           | -m 3200  | --format= | match    |
|           |       |           |           | -a 0     | bcrypt    | (100)    |
|           |       |           |           | hash.txt | --wordl.. |          |
|           |       |           |           | wordlis. | hash.txt  |          |
+-----------------------------------------------------------------------------+
```

### 2. Configure Wordlist

```bash
# Set default wordlist
python -m smartcrack config --wordlist /path/to/rockyou.txt

# View current config
python -m smartcrack config --show

# Reset to defaults
python -m smartcrack config --reset
```

### 3. Crack Passwords (Manual Workflow)

```bash
# Auto-detect mode from identification, use hashcat
python -m smartcrack crack --toolname hashcat --wordlist rockyou.txt hash.txt

# Auto-detect format from identification, use john
python -m smartcrack crack --toolname john --wordlist rockyou.txt hash.txt

# Override hashcat mode if auto-detection is wrong
python -m smartcrack crack --toolname hashcat --hashcat-mode 0 --wordlist rockyou.txt hash.txt

# Override john format
python -m smartcrack crack --toolname john --john-format raw-md5 --wordlist rockyou.txt hash.txt

# Use saved wordlist (from config)
python -m smartcrack crack --toolname hashcat hash.txt

# Brute-force mask attack (hashcat only)
python -m smartcrack crack --toolname hashcat --mask '?a?a?a?a?a?a' hash.txt

# Use rules file (john only)
python -m smartcrack crack --toolname john --rules /path/to/rules.txt --wordlist rockyou.txt hash.txt
```

### Crack Command Options

| Option | Required | Description |
|--------|----------|-------------|
| `--toolname`, `-t` | **Yes** | `hashcat` or `john` |
| `--wordlist`, `-w` | Yes* | Path to wordlist (uses saved default if omitted) |
| `--hashcat-mode`, `-m` | No | Override auto-detected hashcat mode |
| `--john-format`, `-f` | No | Override auto-detected john format |
| `--mask` | No | Hashcat mask for brute-force (implies `-a 3`) |
| `--rules` | No | Path to rules file (john only) |

*Required unless `--mask` is used.

---

## 🏗️ Architecture

```text
smartcrack/
├── cli.py                      # Typer + Rich CLI (identify, config, crack)
├── models.py                   # Shared dataclasses (HashCandidate, etc.)
├── __main__.py                 # Entry point
├── __init__.py
├── config/
│   ├── settings.py            # Pydantic Settings (typed config)
│   ├── legacy.py              # JSON migration layer
│   └── store.py               # Compatibility wrappers
├── detectors/
│   └── input_detector.py      # Input type detection (magic bytes)
├── extractors/
│   └── john_extractors.py     # Hash extraction from archives
├── identifiers/
│   ├── hash_identifier.py     # Hash type identification (patterns.json)
│   └── patterns.json          # 70+ regex patterns with metadata
├── sessions/
│   └── store.py               # Session logging (JSONL)
├── utils/
│   └── subprocess_safe.py     # Secure subprocess handling
└── tests/
    ├── test_identifier.py     # Unit tests for hash identification
    └── test_cli.py            # Config + identifier integration tests
```

### Data Flow

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

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run identifier tests only
python -m pytest tests/test_identifier.py -v

# Run config/CLI tests
python -m pytest tests/test_cli.py -v

# Type checking
python -m mypy smartcrack

# Linting
python -m ruff check smartcrack
```

### Test Files Included
- `example_hashes.txt` - Sample hashes in various formats (MD5, SHA1, SHA256, bcrypt, NTLM, etc.)
- `wordlist_sample.txt` - 50 common passwords for testing

---

## 📝 Configuration

Configuration is stored at `~/.smartcrack/config.json`:

```json
{
  "default_wordlist": "/path/to/rockyou.txt",
  "wordlists": ["/path/to/rockyou.txt", "/other/list.txt"],
  "preferred_tool": null,
  "timeout_seconds": 3600,
  "session_dir": "C:\\Users\\user\\.smartcrack\\sessions"
}
```

### Environment Variables
All settings support `SMARTCRACK_` prefix:
```bash
export SMARTCRACK_DEFAULT_WORDLIST=/path/to/wordlist.txt
export SMARTCRACK_TIMEOUT_SECONDS=7200
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `hashcat: command not found` | Install hashcat: `sudo apt-get install hashcat` |
| `john: command not found` | Install John: `sudo apt-get install john` |
| Hash not identified | Check hash format; try `identify --json` for raw output |
| Crack runs but finds nothing | Try larger wordlist (e.g., rockyou.txt) or different mask |
| Permission denied on config | Ensure `~/.smartcrack/` directory exists |
| Oracle hash not detected | Oracle hashes are 48-60 hex chars; ensure format matches |

---

## 📈 Roadmap & Limitations

### Current Limitations
- Extractor coverage is basic (PDF, ZIP, RAR, 7z, Office, SSH)
- Hash identification is pattern-based (no ML)
- No distributed cracking
- No resume capability for interrupted cracks (session logging only)

### Planned
- Resume from session
- Progress reporting for long cracks
- Plugin system for custom extractors/identifiers
- More archive format support

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **New Extractors**: Add support for more archive formats
2. **Hash Types**: Extend `patterns.json` with new pattern matchers
3. **Performance**: Optimize identification for large hash lists
4. **Documentation**: Expand examples and guides
5. **Tests**: Add integration tests with mocked backends

---

## 📄 License

MIT License - See LICENSE file for details

---

## ⚖️ Legal Disclaimer

This tool is for **authorized security testing and educational purposes only**. Unauthorized access to computer systems is illegal. Users are responsible for:

- Obtaining proper authorization before testing
- Complying with all applicable laws and regulations
- Using this tool ethically and responsibly
- Respecting privacy and security

The developers assume no liability for misuse or damage caused by this tool.

---

## 📧 Support

For issues, questions, or suggestions:

- Open a GitHub Issue
- Check existing issues for similar problems
- Provide detailed error messages and reproduction steps

---

**Happy Cracking! 🔐** (with proper authorization, of course)