# Local development handler (Windows PowerShell)
#
# Goals
# - Create and use a dedicated venv at repo root (./.venv) to avoid path/watch issues
# - Install backend requirements idempotently
# - Load environment from .env (if present)
# - Start FastAPI via the venv's python directly (no Activate.ps1 needed)
# - Keep working directory correct so "app" is importable
#
# Usage (from repo root):
#   ./local.ps1 backend             # run API with reload on port 8000
#   ./local.ps1 backend -Port 9000  # run API on a different port
#   ./local.ps1 frontend            # run Svelte dev server (uses Bun if available)
#   ./local.ps1 up                  # run backend + frontend
#   ./local.ps1 pip "install httpx==0.25.0"  # run pip within venv

[CmdletBinding()]
Param(
  [Parameter(Position=0)] [ValidateSet('backend','frontend','up','types','pip')] [string] $Command = 'backend',
  [int] $Port = 8000
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

$RepoRoot = Split-Path -Parent $PSCommandPath
$VenvDir = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts/python.exe'

function Get-PythonCommand {
  $python = $null
  if (Get-Command python -ErrorAction SilentlyContinue) { $python = 'python' }
  elseif (Get-Command py -ErrorAction SilentlyContinue) { $python = 'py -3' }
  else { throw 'Python not found. Install Python 3.10+ and ensure it is on PATH.' }
  return $python
}

function New-VenvIfMissing {
  if (-not (Test-Path $VenvDir)) {
    Write-Info 'Creating venv in ./.venv...'
    $python = Get-PythonCommand
    & $python -m venv $VenvDir | Out-Null
  }
}

function Invoke-VenvPip([string[]] $PipArgs) {
  & $VenvPython -m pip @PipArgs
}

function Install-BackendRequirements {
  New-VenvIfMissing
  Write-Info 'Ensuring backend requirements are installed...'
  $req = Join-Path $RepoRoot 'backend/requirements.txt'
  Invoke-VenvPip @('install','-q','-r', $req)
}

function Import-DotEnv {
  $dotenv = Join-Path $RepoRoot '.env'
  if (Test-Path $dotenv) {
    Write-Info 'Loading environment from .env'
    Get-Content $dotenv | ForEach-Object {
      if ($_ -match '^(\s*#|\s*$)') { return }
      $kv = $_ -split '=',2
      if ($kv.Length -eq 2) {
        $name = $kv[0].Trim(); $val = $kv[1].Trim()
        # Strip surrounding quotes if any
        if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length-2) }
        if ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Substring(1, $val.Length-2) }
        Set-Item -Path ("Env:" + $name) -Value $val
      }
    }
  }
}

function New-InstanceDirIfMissing {
  $instanceDir = Join-Path $RepoRoot 'instance'
  if (-not (Test-Path $instanceDir)) { New-Item -ItemType Directory -Path $instanceDir | Out-Null }
}

function Start-Backend {
  Install-BackendRequirements
  Import-DotEnv
  New-InstanceDirIfMissing

  $backendDir = Join-Path $RepoRoot 'backend'
  $env:PYTHONPATH = '.'  # so that "app" is importable when cwd=backend

  Write-Ok "Starting FastAPI on http://localhost:$Port (reload)"
  Push-Location $backendDir
  try {
    & $VenvPython -m uvicorn app.main:app --reload --port $Port
  }
  finally { Pop-Location }
}

function Start-Frontend {
  $frontendDir = Join-Path $RepoRoot 'scoracle-svelte'
  Push-Location $frontendDir
  try {
    # Check if Bun is available (check PATH first, then user profile)
    $bunInPath = Get-Command bun -ErrorAction SilentlyContinue
    $bunUserPath = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'
    
    if ($bunInPath) {
      $bunCmd = 'bun'
      $useBun = $true
    } elseif (Test-Path $bunUserPath) {
      $bunCmd = $bunUserPath
      $useBun = $true
    } else {
      $useBun = $false
    }
    
    if ($useBun) {
      if (-not (Test-Path 'node_modules')) { 
        Write-Info 'Installing frontend deps with Bun...'
        & $bunCmd install
      }
      Write-Ok 'Starting Svelte dev server on http://localhost:5173 (Bun)'
      & $bunCmd run dev
    } else {
      Write-Warn 'Bun not found. Install from https://bun.sh for faster builds'
      if (-not (Test-Path 'node_modules')) { 
        Write-Info 'Installing frontend deps with npm...'
        npm install
      }
      Write-Ok 'Starting Svelte dev server on http://localhost:5173'
      npm run dev
    }
  }
  finally { Pop-Location }
}

function Invoke-OpenApiTypes {
  Write-Warn 'OpenAPI types generation not yet configured for Svelte frontend'
  Write-Info 'You can manually generate types or add api:types script to scoracle-svelte/package.json'
}

switch ($Command) {
  'backend' { Start-Backend }
  'frontend' { Start-Frontend }
  'types' { Invoke-OpenApiTypes }
  'up' {
    $job = Start-Job { & powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "& '$using:RepoRoot/local.ps1' backend -Port $using:Port" }
    Start-Sleep -Seconds 2
    Start-Frontend
    Receive-Job $job -Keep
  }
  'pip' {
    if ($args.Count -eq 0) { Write-Warn 'Usage: ./local.ps1 pip "<args>"'; break }
    Install-BackendRequirements
    Write-Ok ("pip " + ($args -join ' '))
    Invoke-VenvPip $args
  }
}
