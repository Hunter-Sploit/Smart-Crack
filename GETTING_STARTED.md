# Getting Started with SmartCrack

Welcome to **SmartCrack**! This guide walks you through setup, hash identification, cracking workflows, and troubleshooting common issues.

---

## ⚡ 1-Minute Quick Start

### Linux & macOS

```bash
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack

# Run the automated installer (creates .venv & installs dependencies)
./install.sh

# Start using SmartCrack!
source .venv/bin/activate
smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'
```

*Don't want to manually activate `.venv`? Use the wrapper script directly:*
```bash
./run.sh identify example_hashes.txt
./run.sh crack example_hashes.txt
```

---

### Windows

#### Command Prompt (cmd)
```cmd
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
install.bat
.venv\Scripts\activate
smartcrack identify example_hashes.txt
```

#### PowerShell
```powershell
git clone https://github.com/Hunter-Sploit/Smart-Crack.git
cd Smart-Crack
.\install.ps1
.\.venv\Scripts\Activate.ps1
smartcrack identify example_hashes.txt
```

*Or run directly without activation:*
```cmd
run.bat identify example_hashes.txt
run.bat crack example_hashes.txt
```

---

## 💡 About `.venv` (Virtual Environments)

> [!NOTE]
> **Why is `.venv/` not committed into Git?**
> A Python virtual environment contains machine-specific absolute file paths and pre-compiled binaries compiled for your specific operating system (Linux vs Windows vs macOS) and Python version.
>
> If a `.venv` directory from one machine is shared to another computer, Python breaks immediately with `bad interpreter` or missing path errors.
>
> The included `install.sh` / `install.bat` / `install.ps1` scripts automatically generate a 100% compatible `.venv` specifically for your computer in under 10 seconds.

---

## 🛠️ Installing Cracking Backends

SmartCrack identifies hashes and auto-generates optimized commands for **Hashcat** (GPU/CPU) and **John the Ripper** (CPU). To run the actual cracking tasks, make sure either tool is installed on your system.

### Ubuntu / Debian / Kali Linux
```bash
sudo apt-get update
sudo apt-get install -y hashcat john john-data
```

### macOS (Homebrew)
```bash
brew install hashcat john
```

### Windows
- **Hashcat**: Download the latest release from [hashcat.net](https://hashcat.net/hashcat/) and extract it to a folder in your `PATH`.
- **John the Ripper**: Download Windows binaries from [openwall.com/john](https://www.openwall.com/john/).

---

## 🚀 Usage Guide

### 1. Identifying Hashes (`smartcrack identify`)

SmartCrack identifies over 70+ hash formats with confidence ratings, Hashcat modes, John formats, and ready-to-run commands.

#### Identify a single hash string:
> [!IMPORTANT]
> If your hash contains `$` signs (like bcrypt, sha512crypt, etc.), **always wrap it in single quotes (`'...'`) in bash/zsh** so your shell does not treat `$2b` or `$6` as bash variables!

```bash
smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'
```

#### Identify from credential dumps or shadow files:
SmartCrack automatically detects and parses structured formats:
- **Linux `/etc/shadow`**:
  ```bash
  smartcrack identify 'root:$6$rounds=5000$salt$hash:18000:0:99999:7:::'
  ```
- **Windows pwdump / SAM**:
  ```bash
  smartcrack identify 'Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::'
  ```
- **User:Hash format**:
  ```bash
  smartcrack identify 'admin:5f4dcc3b5aa765d61d8327deb882cf99'
  ```

#### Identify a list of hashes from a file:
```bash
smartcrack identify example_hashes.txt
```

#### Interactive Mode:
If you run `smartcrack identify` without arguments, SmartCrack will politely prompt you to enter the hash or file path:
```bash
smartcrack identify
# Prompt: Enter hash, dump line, or file path to identify:
```

#### JSON Output (for scripting and pipelines):
```bash
smartcrack identify example_hashes.txt --json
```

---

### 2. Cracking Hashes (`smartcrack crack`)

SmartCrack automatically detects available tools (`hashcat` or `john`), infers the correct hash algorithm, and selects a wordlist.

#### Simple Auto-Crack:
```bash
smartcrack crack example_hashes.txt
```
SmartCrack will:
1. Detect hash format (e.g. MD5 mode 0).
2. Check whether `hashcat` or `john` is installed and pick the best one.
3. Use your configured default wordlist, or fall back to `wordlist_sample.txt` or system wordlists (`rockyou.txt`).
4. Execute safely without shell injection.

#### Manual Tool Choice:
```bash
# Force hashcat
smartcrack crack -t hashcat -w wordlist_sample.txt example_hashes.txt

# Force john
smartcrack crack -t john -w wordlist_sample.txt example_hashes.txt
```

#### Brute-force / Mask Attack:
```bash
# 4-digit PIN brute-force with Hashcat
smartcrack crack -m 0 --mask '?d?d?d?d' hash.txt
```

---

### 3. Persistent Configuration (`smartcrack config`)

Set a default wordlist once so you never have to specify `--wordlist` again:
```bash
# Set your favorite wordlist (e.g. rockyou.txt)
smartcrack config --wordlist /usr/share/wordlists/rockyou.txt

# View current settings
smartcrack config --show

# Reset configuration to defaults
smartcrack config --reset
```

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q: Why did identification fail when I pasted a hash starting with `$2b$`?
**A:** In Bash and Zsh, unquoted `$2b` is evaluated as an empty shell variable! Always wrap hashes in single quotes:
```bash
# Correct:
smartcrack identify '$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u'

# Or let SmartCrack prompt you:
smartcrack identify
```

### Q: Why did I get "Neither hashcat nor john was found in PATH"?
**A:** SmartCrack is an intelligent identification and orchestrator engine. To perform cracking operations, install `hashcat` or `john`:
- Debian/Ubuntu: `sudo apt install hashcat john`
- macOS: `brew install hashcat john`

### Q: How do I crack protected archives (ZIP, PDF, Office, SSH)?
**A:** SmartCrack integrates with `john` extractors (`zip2john`, `pdf2john`, `office2john`, `ssh2john`). Simply point `smartcrack crack` at the protected archive file:
```bash
smartcrack crack protected_file.pdf
```
SmartCrack will extract the hash into a temporary file, identify the format, and launch the cracking process.
