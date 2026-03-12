#!/usr/bin/env bash
set -euo pipefail
TMP_FILE="$(mktemp --suffix=.py)"
cat > "$TMP_FILE" <<'PY'
import importlib
for name in ["openai", "requests", "tqdm", "pycsp3"]:
    importlib.import_module(name)
print("python dependencies: ok")
PY
python "$TMP_FILE"
rm -f "$TMP_FILE"
