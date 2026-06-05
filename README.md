# SmartCrack

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SmartCrack** is a modular, intelligent password cracking framework that automates detection, extraction, identification, and orchestration across Hashcat and John the Ripper. It evolved from a PDF-only cracker into a comprehensive security testing tool.

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

# Test with sample files
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'
python -m smartcrack crack example_hashes.txt --wordlist wordlist_sample.txt
```

---

## ✨ Key Features

- **🔍 Smart Input Detection**: Automatically detects input type via magic bytes and heuristics
  - Encrypted archives (PDF, ZIP, RAR, 7z)
  - Hash dumps (MD5, SHA1, SHA256, bcrypt, NTLM, etc.)
  - Raw plaintext hashes or files
  
- **🎯 Automatic Extractor Routing**: Routes to appropriate extractors
  - `pdf2john`, `zip2john`, `rar2john`, `7z2john` (when available)
  - Extracts hashes from protected archives automatically
  
- **🔎 Hash Identification**: Identifies hash types with confidence scoring
  - Displays hashcat mode and john format hints
  - Supports multiple hash types simultaneously
  
- **⚙️ Intelligent Backend Planner**: Selects optimal cracking engine
  - Prefers Hashcat for GPU-accelerated modes
  - Falls back to John the Ripper when appropriate
  
- **📝 Configuration Management**: Persistent wordlist and preference storage
  - `~/.smartcrack/config.json` for user preferences
  - Centralized wordlist management
  
- **📊 Session Logging**: Complete audit trail and resume capability
  - `~/.smartcrack/sessions/*.json` for forensics and history
  - Resume interrupted cracks
  
- **🛡️ Safe Subprocess Handling**: No shell injection vulnerabilities
  - Argument list-based execution
  - Secure subprocess communication
  
- **🎛️ Single CLI Entrypoint**: Easy-to-use unified interface
  - Typer + Rich for beautiful, responsive CLI

---

## 📋 Supported Hash Types

| Hash Type | Mode | Example |
|-----------|------|---------|
| MD5 | 0 | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA1 | 100 | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA256 | 1400 | `5e884898da28047151d0e56f8dc62927845f5c520a550de58b9c47af9ad8e217` |
| bcrypt | 3200 | `$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u` |
| NTLMv2 | 5600 | `admin::domain:...` |
| Kerberos | 13100 | `$krb5...` |

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- `hashcat` (optional, for GPU acceleration)
- `john` + extractors like `pdf2john`, `zip2john` (optional, for archive extraction)

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

### 1. **Identify Hash Type**

```bash
# Single hash
python -m smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# Multiple hashes from file
python -m smartcrack identify hashes.txt

# Show detailed info
python -m smartcrack identify example_hashes.txt --verbose
```

### 2. **Configure Wordlist**

```bash
# Set default wordlist
python -m smartcrack config --wordlist /path/to/rockyou.txt

# View current config
python -m smartcrack config --show
```

### 3. **Crack Passwords - Auto Workflow**

```bash
# PDF archive (auto-extracts hashes)
python -m smartcrack crack secret.pdf

# ZIP archive
python -m smartcrack crack archive.zip --wordlist /path/to/custom_wordlist.txt

# Hash file with John backend
python -m smartcrack crack dump.hash --backend john

# Raw hash string
python -m smartcrack crack '$1c8bfe8f801d79745c4631d09fff36c82' --wordlist wordlist.txt

# With custom wordlist
python -m smartcrack crack hashes.txt --wordlist wordlist_sample.txt
```

### 4. **Advanced Cracking Options**

```bash
# Use Hashcat mask attack (brute-force pattern)
python -m smartcrack crack dump.hash --mask '?a?a?a?a?a?a'

# Force specific backend
python -m smartcrack crack hashes.txt --backend hashcat

# Specify Hashcat mode manually
python -m smartcrack crack hashes.txt --hashcat-mode 0

# Use rules file (John)
python -m smartcrack crack dump.hash --rules /path/to/rules.txt
```

---

## 🏗️ Architecture

```text
smartcrack/
├── cli.py                      # Typer + Rich CLI interface
├── models.py                   # Shared dataclasses
├── __main__.py                 # Entry point
├── __init__.py
├── config/
│   └── store.py               # Configuration persistence
├── crackers/
│   └── planner.py             # Backend selection logic
├── detectors/
│   └── input_detector.py      # Input type detection
├── extractors/
│   └── john_extractors.py     # Hash extraction from archives
├── identifiers/
│   └── hash_identifier.py     # Hash type identification
├── sessions/
│   └── store.py               # Session logging & resume
└── utils/
    └── subprocess_safe.py     # Secure subprocess handling
```

### Data Flow

```
User Input → Detector → Extractor → Identifier → Planner → Cracker → Results
```

1. **Detector**: Identifies input type (file, hash, archive)
2. **Extractor**: Extracts hashes from archives if needed
3. **Identifier**: Determines hash algorithm and parameters
4. **Planner**: Selects optimal cracking backend (Hashcat/John)
5. **Cracker**: Executes cracking with wordlist/mask
6. **Logger**: Records session for audit/resume

---

## 🧪 Testing

### Quick Test with Sample Files

```bash
# Test hash identification
python -m smartcrack identify example_hashes.txt

# Test cracking with sample wordlist
python -m smartcrack crack example_hashes.txt --wordlist wordlist_sample.txt

# Test single hash
python -m smartcrack identify 5f4dcc3b5aa765d61d8327deb882cf99
```

### Test Files Included

- `example_hashes.txt` - Sample hashes in various formats (MD5, SHA1, SHA256, bcrypt)
- `wordlist_sample.txt` - 50 common passwords for testing

---

## 📝 Configuration

Configuration is stored at `~/.smartcrack/config.json`:

```json
{
  "default_wordlist": "/path/to/rockyou.txt",
  "preferred_backend": "hashcat",
  "timeout_seconds": 3600,
  "session_dir": "~/.smartcrack/sessions"
}
```

### Configuration Commands

```bash
# Set wordlist
python -m smartcrack config --wordlist /path/to/wordlist.txt

# Show current config
python -m smartcrack config --show

# Reset to defaults
python -m smartcrack config --reset
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `hashcat: command not found` | Install hashcat: `sudo apt-get install hashcat` |
| `pdf2john: command not found` | Install John: `sudo apt-get install john` |
| Hash not identified | Ensure hash format is correct; check `identify --verbose` |
| Crack runs but finds nothing | Try larger wordlist (e.g., rockyou.txt) or different mask |
| Permission denied on config | Ensure `~/.smartcrack/` directory exists: `mkdir -p ~/.smartcrack` |

---

## 📈 Roadmap & Limitations

### Current Limitations
- Extractor coverage is basic but easily extensible
- Hash identification engine is pattern-based (could use ML)
- No distributed cracking (intentional for v1)
- Limited rule/mask documentation

### Planned Improvements
- [ ] Expanded extractor coverage (nested archives, hybrid formats)
- [ ] Probabilistic hash type scoring
- [ ] REST API for integration
- [ ] Web dashboard for campaign management
- [ ] Distributed cracking support
- [ ] GPU farm orchestration

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **New Extractors**: Add support for more archive formats
2. **Hash Types**: Extend identifier with new pattern matchers
3. **Performance**: Optimize backend selection logic
4. **Documentation**: Expand examples and guides
5. **Tests**: Add unit and integration tests

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
