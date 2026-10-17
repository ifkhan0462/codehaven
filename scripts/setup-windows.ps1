$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== CodeHaven Setup (Windows) ===" -ForegroundColor Cyan

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command python)) {
    Write-Error "Python not found. Install Python 3.11+ and retry."
}
if (-not (Test-Command node)) {
    Write-Error "Node.js not found. Install Node 20 LTS and retry."
}

$ollamaCmd = $null
if (Test-Command ollama) {
    $ollamaCmd = "ollama"
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") {
    $ollamaCmd = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
} else {
    Write-Host "Ollama not found. Installing via winget..." -ForegroundColor Yellow
    $winget = Get-Process winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "Another winget install is already running. Waiting..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    }
    if (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") {
        $ollamaCmd = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    } else {
        Write-Error "Ollama install failed. Install manually from https://ollama.com/download"
    }
}

Write-Host "`n[1/4] Python virtual environment..." -ForegroundColor Green
$venvPath = Join-Path $Root "backend\.venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}
& "$venvPath\Scripts\pip.exe" install --upgrade pip
& "$venvPath\Scripts\pip.exe" install -r (Join-Path $Root "backend\requirements.txt")

Write-Host "`n[2/4] Frontend dependencies..." -ForegroundColor Green
Push-Location (Join-Path $Root "frontend")
npm install
Pop-Location

Write-Host "`n[3/4] Pulling Ollama models (requires internet)..." -ForegroundColor Green
& $ollamaCmd pull qwen2.5-coder:7b
& $ollamaCmd pull nomic-embed-text

Write-Host "`n[4/4] Verifying Ollama..." -ForegroundColor Green
& $ollamaCmd list

Write-Host "`n=== Setup complete! ===" -ForegroundColor Cyan
Write-Host "Run: .\scripts\dev.ps1" -ForegroundColor White
