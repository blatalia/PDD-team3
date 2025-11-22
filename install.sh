#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "Start virtual enviroment (.venv)..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating run.sh..."

cat > run.sh << 'EOF'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 main.py
EOF

chmod +x run.sh

echo "[*] Desktop shortcut creating"

DESKTOP_FILE="$HOME/Desktop/PhotonicsApp.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Exec=$SCRIPT_DIR/run.sh
Name=Photonics App
Comment=Photonics App PDP team 3
Icon=$SCRIPT_DIR/icon.png
EOF

chmod +x "$DESKTOP_FILE"

echo
echo "=============================================="
echo " Installation Finished."
echo " - to run run: ./run.sh"
echo " - or run it via clicking the icon 'Photonics App' on your desktop"
echo "=============================================="
