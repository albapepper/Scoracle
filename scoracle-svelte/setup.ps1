# Scoracle Svelte Setup Script
# Run this from the scoracle-svelte directory

Write-Host "Setting up Scoracle Svelte..." -ForegroundColor Green

# Copy static data files
Write-Host "Copying data files..." -ForegroundColor Yellow
Copy-Item -Path "..\frontend\public\data\*.json" -Destination ".\static\data\" -Force
Copy-Item -Path "..\frontend\public\scoracle-logo.png" -Destination ".\static\" -Force

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run 'npm run dev' to start the development server" -ForegroundColor Cyan

