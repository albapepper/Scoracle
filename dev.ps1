<#
PowerShell helper script for local dev.
Usage (from repo root):
  ./dev.ps1 up        # start backend (reload) and frontend
  ./dev.ps1 backend   # start backend only
  ./dev.ps1 frontend  # start frontend only (expects backend running)
  ./dev.ps1 types     # generate OpenAPI TS types
#>
Param(
  [Parameter(Position=0)][string]$Command = 'up'
)

function Ensure-Venv {
  if (-Not (Test-Path 'backend/venv')) {
    Write-Host 'Creating Python venv...' -ForegroundColor Cyan
    python -m venv backend/venv
  }
}

function Start-Backend {
  Ensure-Venv
  & backend/venv/Scripts/Activate.ps1
  pip install -q -r backend/requirements.txt
  $env:PYTHONPATH = 'backend/app'
  Write-Host 'Starting FastAPI (uvicorn)...' -ForegroundColor Green
  uvicorn app.main:app --reload --port 8000
}

function Start-Frontend {
  Push-Location frontend
  if (-Not (Test-Path 'node_modules')) { npm install }
  Write-Host 'Starting React dev server...' -ForegroundColor Green
  npm start
  Pop-Location
}

function Generate-Types {
  Push-Location frontend
  if (-Not (Test-Path 'node_modules')) { npm install }
  npm run api:types
  Pop-Location
}

switch ($Command) {
  'backend' { Start-Backend }
  'frontend' { Start-Frontend }
  'types' { Generate-Types }
  'up' {
    $backend = Start-Job { & powershell -NoLogo -NoProfile -Command "Import-Module '$PSScriptRoot/dev.ps1'; Start-Backend" }
    Start-Sleep -Seconds 3
    Start-Frontend
    Receive-Job $backend -Keep
  }
  default { Write-Host "Unknown command: $Command" -ForegroundColor Red }
}
