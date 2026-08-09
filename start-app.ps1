# FinCore Bank - Unified Application Startup Script (Windows PowerShell)
# Starts both Backend API and Frontend UI concurrently

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FinCore Bank - Application Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/4] Checking prerequisites..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version
    Write-Host "  [OK] Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js not found. Please install Node.js 20+" -ForegroundColor Red
    exit 1
}

try {
    $npmVersion = npm --version
    Write-Host "  [OK] npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] npm not found" -ForegroundColor Red
    exit 1
}

# Setup Backend API
Write-Host ""
Write-Host "[2/4] Setting up Backend API..." -ForegroundColor Yellow
Set-Location app

if (-Not (Test-Path "node_modules")) {
    Write-Host "  Installing backend dependencies..." -ForegroundColor Blue
    npm install --silent
}

if (-Not (Test-Path ".env")) {
    Write-Host "  Creating .env from template..." -ForegroundColor Blue
    Copy-Item .env.example .env
}

Write-Host "  [OK] Backend ready" -ForegroundColor Green

# Setup Frontend UI
Write-Host ""
Write-Host "[3/4] Setting up Frontend UI..." -ForegroundColor Yellow
Set-Location client

if (-Not (Test-Path "node_modules")) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Blue
    npm install --silent
}

if (-Not (Test-Path ".env")) {
    Write-Host "  Creating .env from template..." -ForegroundColor Blue
    Copy-Item .env.example .env
}

Write-Host "  [OK] Frontend ready" -ForegroundColor Green

Set-Location ..\..

# Create logs directory
if (-Not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start services
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend API:       http://localhost:4000/api/v1" -ForegroundColor Green
Write-Host "Swagger Docs:      http://localhost:4000/api/docs" -ForegroundColor Green
Write-Host "Frontend UI:       http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Database:          localhost:5432 (ensure PostgreSQL is running)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Blue
Write-Host ""

# Start Backend API
Write-Host "[Backend API] Starting on port 4000..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\app
    npm run dev 2>&1 | Out-File -FilePath ..\logs\backend.log -Append
}

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend UI
Write-Host "[Frontend UI] Starting on port 3000..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\app\client
    npm run dev 2>&1 | Out-File -FilePath ..\..\logs\frontend.log -Append
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  [OK] All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Logs:" -ForegroundColor Blue
Write-Host "  Backend:  logs\backend.log"
Write-Host "  Frontend: logs\frontend.log"
Write-Host ""
Write-Host "Services are running in background jobs" -ForegroundColor Yellow
Write-Host "To stop: Run 'Get-Job | Stop-Job' and 'Get-Job | Remove-Job'" -ForegroundColor Yellow
Write-Host ""

# Keep script running and show logs
Write-Host "Monitoring services (Ctrl+C to exit)..." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        if ((Get-Job -Id $backendJob.Id).State -eq "Failed") {
            Write-Host "Backend API failed! Check logs\backend.log" -ForegroundColor Red
            break
        }
        if ((Get-Job -Id $frontendJob.Id).State -eq "Failed") {
            Write-Host "Frontend UI failed! Check logs\frontend.log" -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}
