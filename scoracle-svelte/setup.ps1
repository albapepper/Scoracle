# Scoracle Svelte Setup Script
# Run this from the scoracle-svelte directory

Write-Host "Setting up Scoracle Svelte..." -ForegroundColor Green

# Copy static data files
Write-Host "Copying data files..." -ForegroundColor Yellow
Copy-Item -Path "..\frontend\public\data\*.json" -Destination ".\static\data\" -Force
Copy-Item -Path "..\frontend\public\scoracle-logo.png" -Destination ".\static\" -Force

# Install dependencies with bun (or npm as fallback)
Write-Host "Installing dependencies..." -ForegroundColor Yellow
$bunInPath = Get-Command bun -ErrorAction SilentlyContinue
$bunUserPath = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'

if ($bunInPath) {
    bun install
} elseif (Test-Path $bunUserPath) {
    & $bunUserPath install
} else {
    Write-Host "Bun not found, using npm..." -ForegroundColor Yellow
    npm install
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run './local.ps1 frontend' from the repo root to start the dev server" -ForegroundColor Cyan

