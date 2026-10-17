$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== CodeHaven Dev Server ===" -ForegroundColor Cyan

$venvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual env missing. Running setup first..." -ForegroundColor Yellow
    & (Join-Path $Root "scripts\setup-windows.ps1")
}

Write-Host "Starting frontend (Vite + Electron; Electron spawns the backend)..." -ForegroundColor Green
Push-Location (Join-Path $Root "frontend")
try {
    npm run dev
} finally {
    Pop-Location
}
