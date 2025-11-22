@echo off
setlocal

REM -----------------------------------------------------------
REM  Resolve the absolute path to the repository directory
REM -----------------------------------------------------------
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [*] Creating virtual environment .venv...

if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [*] Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo [*] Creating run.bat launcher...

(
echo @echo off
echo set SCRIPT_DIR=%%~dp0
echo cd /d "%%SCRIPT_DIR%%"
echo call .venv\Scripts\activate.bat
echo python main.py
) > run.bat

REM -----------------------------------------------------------
REM  Create desktop shortcut (.lnk) using PowerShell + COM
REM -----------------------------------------------------------

echo [*] Creating desktop shortcut...

REM Resolve desktop path
set DESKTOP_PATH=%USERPROFILE%\Desktop

REM Shortcut target paths
set SHORTCUT_PATH=%DESKTOP_PATH%\Photonics App.lnk
set TARGET=%SCRIPT_DIR%run.bat
set ICON=%SCRIPT_DIR%icon.ico

REM PowerShell COM automation to generate .lnk shortcut
powershell.exe -NoProfile -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');" ^
  "$s.TargetPath='%TARGET%';" ^
  "$s.IconLocation='%ICON%';" ^
  "$s.WorkingDirectory='%SCRIPT_DIR%';" ^
  "$s.Save()"

echo.
echo ========================================================
echo  Installation finished!
echo  - Launch using: run.bat
echo  - Or click the 'Photonics App' shortcut on your desktop
echo ========================================================

pause
endlocal
