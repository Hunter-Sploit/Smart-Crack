@echo off
REM SmartCrack Quick Installation Script for Windows
echo ==========================================
echo        SmartCrack Windows Installer
echo ==========================================

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Error: Python is not detected in PATH.
    echo     Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Setup Virtual Environment
if not exist ".venv" (
    echo [+] Creating virtual environment in .venv ...
    python -m venv .venv
) else (
    echo [+] Virtual environment .venv already exists.
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
echo [+] Upgrading pip and installing requirements...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet

echo ==========================================
echo        Installation Complete!
echo ==========================================
echo To start using SmartCrack:
echo   1. Activate the virtual environment:
echo        .venv\Scripts\activate
echo   2. Run SmartCrack:
echo        smartcrack identify example_hashes.txt
echo        smartcrack crack example_hashes.txt
echo.
pause
