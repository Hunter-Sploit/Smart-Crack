#!/usr/bin/env bash
# SmartCrack Quick Installation Script for Linux and macOS
set -e

echo "=========================================="
echo "       SmartCrack Installer"
echo "=========================================="

# 1. Check Python
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[!] Error: Python 3 is not installed or not in PATH."
    echo "    Please install Python 3.9 or higher and rerun this script."
    exit 1
fi

PY_VERSION=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[+] Detected Python: $PYTHON_BIN (version $PY_VERSION)"

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[+] Creating virtual environment in .venv/ ..."
    $PYTHON_BIN -m venv .venv
else
    echo "[+] Virtual environment .venv/ already exists."
fi

# Activate virtual environment
# shellcheck source=/dev/null
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "[+] Upgrading pip and installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet

echo "[+] SmartCrack CLI installed successfully into .venv!"

# 4. Check system cracking tools
echo ""
echo "--- Checking Cracking Tools ---"
if command -v hashcat >/dev/null 2>&1; then
    echo "[✓] hashcat detected: $(command -v hashcat)"
else
    echo "[-] hashcat not detected in PATH (optional for GPU cracking)."
    echo "    Install with: sudo apt-get install hashcat (Ubuntu/Debian) or brew install hashcat (macOS)"
fi

if command -v john >/dev/null 2>&1; then
    echo "[✓] john detected: $(command -v john)"
else
    echo "[-] john (John the Ripper) not detected in PATH."
    echo "    Install with: sudo apt-get install john john-data (Ubuntu/Debian) or brew install john (macOS)"
fi

echo ""
echo "=========================================="
echo "          Installation Complete!"
echo "=========================================="
echo ""
echo "To get started:"
echo "  1. Activate the environment:"
echo "       source .venv/bin/activate"
echo ""
echo "  2. Run SmartCrack:"
echo "       smartcrack identify '5f4dcc3b5aa765d61d8327deb882cf99'"
echo "       smartcrack crack example_hashes.txt"
echo ""
echo "  Or run directly without activating:"
echo "       ./run.sh identify example_hashes.txt"
echo ""
