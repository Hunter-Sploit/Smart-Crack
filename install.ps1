# SmartCrack PowerShell Installation Script
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     SmartCrack PowerShell Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "[!] Error: Python 3 was not found in PATH." -ForegroundColor Red
    Write-Host "    Please install Python 3.9+ from https://www.python.org/ or the Microsoft Store."
    exit 1
}

Write-Host "[+] Found Python: $($python.Source)" -ForegroundColor Green

# Create .venv if not present
if (-not (Test-Path ".venv")) {
    Write-Host "[+] Creating virtual environment in .venv ..." -ForegroundColor Yellow
    & $python.Source -m venv .venv
} else {
    Write-Host "[+] Virtual environment .venv already exists." -ForegroundColor Green
}

# Install dependencies
Write-Host "[+] Installing dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\pip.exe install -r requirements.txt --quiet
& .\.venv\Scripts\pip.exe install -e . --quiet

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "        Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "To use SmartCrack:"
Write-Host "  1. Activate virtual environment:"
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "  2. Run SmartCrack:"
Write-Host "     smartcrack identify example_hashes.txt" -ForegroundColor Yellow
Write-Host "     smartcrack crack example_hashes.txt" -ForegroundColor Yellow
Write-Host ""
