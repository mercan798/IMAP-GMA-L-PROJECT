#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/daisy/gmail"
VENV_PY="$APP_DIR/venv/bin/python"
APP_FILE="$APP_DIR/uı.py"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Python not found at $VENV_PY" >&2
  exit 1
fi

cd "$APP_DIR"
exec "$VENV_PY" "$APP_FILE"
