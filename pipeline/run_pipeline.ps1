# FinCore Bank - PySpark Pipeline Execution Script (Windows PowerShell)
# This script runs the data pipeline locally on Windows.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("good_data", "bad_data")]
    [string]$DataFolder
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FinCore Bank - Data Pipeline (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (-Not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Python is installed but not working correctly" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Python: $pythonVersion" -ForegroundColor Green

# Check Java
if (-Not (Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] Java not found. Please install Java JDK 11 or 17" -ForegroundColor Red
    exit 1
}

$javaVersionOutput = java --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Java is installed but not working correctly" -ForegroundColor Red
    exit 1
}

$javaVersionLine = $javaVersionOutput | Select-Object -First 1
Write-Host "  [OK] Java: $javaVersionLine" -ForegroundColor Green

# Check virtual environment
Write-Host ""
Write-Host "[2/5] Setting up Python virtual environment..." -ForegroundColor Yellow

if (-Not (Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

Write-Host "  Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "  [OK] Dependencies installed" -ForegroundColor Green

# Check data folder
Write-Host ""
Write-Host "[4/5] Validating data folder..." -ForegroundColor Yellow

$dataRoot = Join-Path -Path ".." -ChildPath "data"
$dataPath = Join-Path -Path $dataRoot -ChildPath $DataFolder
if (-Not (Test-Path $dataPath)) {
    Write-Host "  [ERROR] Data folder not found: $dataPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please generate datasets first:" -ForegroundColor Yellow
    Write-Host "  cd data" -ForegroundColor Gray
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "  python generate_data.py" -ForegroundColor Gray
    exit 1
}
Write-Host "  [OK] Data folder found: $dataPath" -ForegroundColor Green

# Check database configuration
Write-Host ""
Write-Host "[5/5] Checking database connectivity..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
}

$dbHost = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$dbPort = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }
Write-Host "  Database: $dbHost`:$dbPort" -ForegroundColor Gray

# Run pipeline
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running PySpark Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python ingest.py $DataFolder

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Pipeline completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Pipeline failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    exit 1
}
