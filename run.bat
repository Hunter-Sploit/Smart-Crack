@echo off
REM SmartCrack Windows Runner - runs directly using .venv
set DIR=%~dp0
if exist "%DIR%.venv\Scripts\smartcrack.exe" (
    "%DIR%.venv\Scripts\smartcrack.exe" %*
) else if exist "%DIR%.venv\Scripts\python.exe" (
    "%DIR%.venv\Scripts\python.exe" -m smartcrack %*
) else (
    echo [!] .venv not found. Running installer first...
    call "%DIR%install.bat"
    "%DIR%.venv\Scripts\smartcrack.exe" %*
)
