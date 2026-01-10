#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Laser Image Analyzer"
APP_ID="lasery-image-analyzer"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REPO_ROOT/venv/bin/python"

ICON_PATH="$REPO_ROOT/assets/icon.png"
DESKTOP_FILE="$HOME/.local/share/applications/${APP_ID}.desktop"
DESKTOP_DIR="$HOME/Desktop"

echo "[1/4] Checking venv..."
if [ ! -x "$PY" ]; then
  echo "ERROR: venv not found at $PY"
  echo "Create it first: python3 -m venv venv"
  exit 1
fi

echo "[2/4] Installing requirements..."
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$REPO_ROOT/requirements.txt"

echo "[3/4] Creating .desktop launcher..."
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=Laser image analysis application
Exec=${REPO_ROOT}/scripts/run_linux.sh
Path=${REPO_ROOT}
Icon=${ICON_PATH}
Terminal=false
Categories=Science;Education;
StartupWMClass=Lasery
EOF

chmod +x "$DESKTOP_FILE"

echo "[4/4] Copying launcher to Desktop (best effort)..."
if [ -d "$DESKTOP_DIR" ]; then
  cp -f "$DESKTOP_FILE" "$DESKTOP_DIR/${APP_ID}.desktop" || true
  chmod +x "$DESKTOP_DIR/${APP_ID}.desktop" || true
fi

echo "DONE."
echo "You can now run the app from system menu or desktop."
