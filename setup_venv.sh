#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "No usable Python interpreter found: ${PYTHON_BIN}" >&2
  exit 1
fi

echo "[1/4] Creating virtual environment: ${VENV_DIR}"
"$PYTHON_BIN" -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[2/4] Upgrading pip"
python -m pip install --upgrade pip

echo "[3/4] Installing dependencies"
pip install -r "${ROOT_DIR}/requirements.txt"

echo "[4/4] Done"
echo "Activation command: source ${VENV_DIR}/bin/activate"
