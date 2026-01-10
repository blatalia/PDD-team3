#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REPO_ROOT/venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "ERROR: venv not found. Run install_linux.sh first."
  exit 1
fi

exec "$PY" -m app.main
