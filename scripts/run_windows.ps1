$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PyExe = Join-Path $RepoRoot "venv\Scripts\python.exe"

if (-not (Test-Path $PyExe)) {
  throw "venv not found. Run install_windows.ps1 first."
}

Set-Location $RepoRoot
& $PyExe -m app.main
