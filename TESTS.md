# SmartCrack - Test Suite & Execution Report

This document outlines the testing methodology, environment configuration, full list of automated unit tests, live CLI end-to-end tests, and containerized isolation test results for the [Smart-Crack](file:///home/hunter/Projects/Smart-Crack) project.

---

## 1. Test Environment Summary

| Component | Host Environment | Container Environment |
| :--- | :--- | :--- |
| **Operating System** | Linux (Kernel 6.18) | Debian 12 (Bookworm / Trixie) |
| **Python Version** | Python 3.14.7 | Python 3.12.15 |
| **Test Framework** | `pytest 9.1.1` + `pytest-mock 3.16.0` | `pytest 9.1.1` + `pytest-mock 3.16.0` |
| **Execution Sandboxing** | Virtualenv (`.venv`) & Bubblewrap (`bwrap`) | Docker Engine (`--network none`) |
| **Total Test Count** | 39 Automated Unit Tests | 39 Automated Unit Tests |
| **Pass Rate** | **100% (39/39 Passed)** | **100% (39/39 Passed)** |
| **Execution Time** | ~0.11s | ~0.11s |

---

## 2. Automated Test Suite (29/29 Unit Tests)

The automated test suite is located in the [`tests/`](file:///home/hunter/Projects/Smart-Crack/tests/) directory and is divided into two primary test suites: [test_cli.py](file:///home/hunter/Projects/Smart-Crack/tests/test_cli.py) and [test_identifier.py](file:///home/hunter/Projects/Smart-Crack/tests/test_identifier.py).

### A. Configuration & CLI Settings (`TestConfig` in `tests/test_cli.py`)

| Test Name | Test Objective | Assertion Details | Result |
| :--- | :--- | :--- | :---: |
| `test_default_config` | Validates default configuration values upon fresh initialization. | Checks that `default_wordlist` is `None`, `timeout_seconds` defaults to `3600`, and `wordlists` is empty. | **PASSED** |
| `test_set_wordlist` | Verifies saving a new default wordlist. | Sets wordlist path `test_wordlist.txt` and verifies it is recorded in configuration store. | **PASSED** |
| `test_pydantic_settings` | Tests schema validation using Pydantic Settings. | Ensures settings model parses environment values and defaults cleanly. | **PASSED** |
| `test_migration_from_json` | Tests backward-compatible configuration migration from legacy JSON. | Injects legacy JSON format, triggers migration loader, and asserts modern schema alignment. | **PASSED** |
| `test_reset_config` | Verifies full configuration reset to defaults. | Resets stored state and verifies that configured wordlists and overrides are cleared. | **PASSED** |

---

### B. Hash Identification Integration (`TestIdentifier` in `tests/test_cli.py`)

| Test Name | Input Sample | Expected Candidates & Attributes | Result |
| :--- | :--- | :--- | :---: |
| `test_md5` | `5f4dcc3b5aa765d61d8327deb882cf99` | Candidates contain `MD5` (`-m 0`, `raw-md5`) and `NTLM`. | **PASSED** |
| `test_sha1` | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` | Candidates contain `SHA1` (`-m 100`) and `RIPEMD-160`. | **PASSED** |
| `test_sha256` | `5e884898da28047151d0e56f8dc62927845f5c520a550de58b9c47af9ad8e217` | Candidates contain `SHA256` (`-m 1400`). | **PASSED** |
| `test_bcrypt` | `$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u` | Identifies `bcrypt` (`-m 3200`) with confidence score > 0.90. | **PASSED** |
| `test_ntlm` | `8846f7eaee8fb117ad06bdd830b7586c` | Identifies 32-hex length ambiguity (`MD5` and `NTLM`). | **PASSED** |
| `test_mysql` | `*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19` | Matches MySQL 5.7+ hash pattern (`-m 7401`). | **PASSED** |
| `test_salted_md5` | `6a204bd8bce90f2a3a9e90a6e47213f8:salt` | Detects salt delimiter and assigns mode 10 / vBulletin. | **PASSED** |
| `test_sha256_crypt` | `$5$salt$eGSigWJlPyHPltF4wY2i7kcD/dANpwKG7hOPOjYL7B5:salt` | Matches modular crypt prefix `$5$` for sha256crypt (`-m 7400`). | **PASSED** |
| `test_oracle` | `EA4D5C2B1672CC9B1567490471E8F67DFF2D4487B2B91948` | Matches Oracle 10g/11g SHA-1 based digest (`-m 3100`). | **PASSED** |
| `test_commands_included` | `5f4dcc3b5aa765d61d8327deb882cf99` + `rockyou.txt` | Generates valid ready-to-run CLI strings for Hashcat and John. | **PASSED** |
| `test_unknown_hash` | `not_a_hash_at_all` | Handled safely; returns empty candidate list or Unknown. | **PASSED** |
| `test_confidence_ordering` | `$2b$12$...` | Confirms candidate array is sorted by confidence descending. | **PASSED** |

---

### C. Hash Identifier Core Logic (`TestHashIdentifier` in `tests/test_identifier.py`)

| Test Name | Focus Area | Description | Result |
| :--- | :--- | :--- | :---: |
| `test_md5` | Pattern Matching | Verifies regex matching against `patterns.json` definitions. | **PASSED** |
| `test_sha1` | Multi-candidate Detection | Validates candidate disambiguation for 40-character hex. | **PASSED** |
| `test_sha256` | 64-char Hex Digest | Tests SHA2-256 standard format matching. | **PASSED** |
| `test_bcrypt` | Modular Crypt Format | Tests `$2a$`, `$2b$`, `$2y$` format confidence scoring. | **PASSED** |
| `test_ntlm` | Windows Hashes | Tests NTLM hash identification against MD5 collisions. | **PASSED** |
| `test_mysql` | Database Hashes | Tests asterisk prefix detection for MySQL SHA-1 double hashing. | **PASSED** |
| `test_salted_md5` | Delimited Inputs | Validates parser handling of `<hash>:<salt>` syntax. | **PASSED** |
| `test_sha256_crypt` | Unix Crypt Hashes | Validates Linux `/etc/shadow` style `$5$` hashes. | **PASSED** |
| `test_oracle` | Database Enterprise Hashes | Validates 48-60 hex characters Oracle database digests. | **PASSED** |
| `test_commands_included` | Shell Command Synthesis | Verifies format templates: `hashcat -m <m> -a 0 ...` and `john --format=<f> ...`. | **PASSED** |
| `test_unknown_hash` | Graceful Degradation | Verifies non-hex and arbitrary strings do not crash the engine. | **PASSED** |
| `test_confidence_ordering` | Score Sorting | Verifies `candidates[0].confidence >= candidates[1].confidence`. | **PASSED** |

---

## 3. End-to-End Live Command Verifications

In addition to unit tests, live integration runs were executed against all CLI subcommands:

### Test 1: Identification Command with Rich Formatting
```bash
python -m smartcrack identify '5f4dcc3b5aa765d61d8327deb882cf99'
```
* **Output:** Clean Rich tabular display listing `MD5` (80% confidence, Hashcat `-m 0`, John `raw-md5`) and `NTLM` (75% confidence, Hashcat `-m 1000`, John `nt`).
* **Status:** **SUCCESS**

### Test 2: Machine-Readable JSON Output
```bash
python -m smartcrack identify '5f4dcc3b5aa765d61d8327deb882cf99' --json
```
* **Output:** Valid JSON array structure containing candidate names, confidence percentages, modes, formats, and synthesized execution strings.
* **Status:** **SUCCESS**

### Test 3: Configuration Read / Write / Reset
```bash
python -m smartcrack config --wordlist wordlist_sample.txt
python -m smartcrack config --show
python -m smartcrack config --reset
```
* **Output:** Correctly mutated `~/.smartcrack/config.json` and reverted settings back to initial defaults.
* **Status:** **SUCCESS**

### Test 4: End-to-End Cracking & Audit Trail Generation
```bash
python -m smartcrack crack 5f4dcc3b5aa765d61d8327deb882cf99 -t john -w wordlist_sample.txt
```
* **Output:** Automatically resolved `raw-md5`, launched John the Ripper safely via argument list, cracked the hash to `password`, and logged session data to `~/.smartcrack/sessions/session_<timestamp>.json`.
* **Status:** **SUCCESS**

---

## 4. Isolated Environment Execution Results

### Docker Container Isolation
A dedicated multi-layer [Dockerfile](file:///home/hunter/Projects/Smart-Crack/Dockerfile) and [docker-compose.yml](file:///home/hunter/Projects/Smart-Crack/docker-compose.yml) were configured.

* **Command Executed:**
  ```bash
  docker run --rm --network none --entrypoint pytest smartcrack:latest tests/ -v
  ```
* **Isolation Guarantees:**
  * Network disabled (`--network none`)
  * Container filesystem isolated from host
  * Disposable container destroyed immediately after exit (`--rm`)
* **Result:** **29/29 tests passed in 0.11s inside the container.**

### Linux Kernel Namespace Sandbox (Bubblewrap)
* **Command Executed:**
  ```bash
  bwrap --ro-bind /usr /usr \
        --ro-bind /lib /lib \
        --ro-bind /lib64 /lib64 \
        --ro-bind /bin /bin \
        --dev /dev \
        --proc /proc \
        --bind /home/hunter/Projects/Smart-Crack /home/hunter/Projects/Smart-Crack \
        --unshare-all \
        /home/hunter/Projects/Smart-Crack/.venv/bin/pytest /home/hunter/Projects/Smart-Crack/tests/ -v
  ```
* **Isolation Guarantees:**
  * Network namespace unshared (no network sockets permitted)
  * PID, IPC, UTS, and cgroup namespaces unshared
  * Host root filesystem mounted strictly read-only (`ro-bind`)
* **Result:** **29/29 tests passed in 0.09s.**
