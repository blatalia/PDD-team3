$ErrorActionPreference = "Stop"

$AppName = "Laser Image Analyzer"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PyExe = Join-Path $RepoRoot "venv\Scripts\python.exe"

Write-Host "[1/4] Checking venv..."
if (-not (Test-Path $PyExe)) {
  throw "venv not found. Create it first: python -m venv venv"
}

Write-Host "[2/4] Installing requirements..."
& $PyExe -m pip install --upgrade pip
& $PyExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Write-Host "[3/4] Creating desktop shortcut..."
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$AppName.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$RunScript = Join-Path $RepoRoot "scripts\run_windows.ps1"

$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments  = "-ExecutionPolicy Bypass -File `"$RunScript`""
$Shortcut.WorkingDirectory = $RepoRoot

$IconIco = Join-Path $RepoRoot "assets\icon.ico"
if (Test-Path $IconIco) {
  $Shortcut.IconLocation = $IconIco
}

$Shortcut.Save()

Write-Host "[4/4] DONE."
Write-Host "Shortcut created on Desktop."
