#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
export CONSTRAINTLLM_RETRIEVAL_CORPUS="${CONSTRAINTLLM_RETRIEVAL_CORPUS:-${ROOT_DIR}/data/knowledge_base.json}"
python -m constraintllm.run_csp --method TOT "$@"
