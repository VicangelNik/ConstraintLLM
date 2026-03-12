#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
METHOD="${1:-}"
SHARDS="${2:-}"

if [[ -z "${METHOD}" || -z "${SHARDS}" ]]; then
  echo "Usage: bash scripts/rerun_failed_shards.sh <COT|RAG|CARM> <shard list, e.g. 3,4>"
  exit 1
fi

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
export http_proxy=""
export https_proxy=""
export all_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export ALL_PROXY=""
export CONSTRAINTLLM_PARALLEL_WORKERS="${CONSTRAINTLLM_PARALLEL_WORKERS:-4}"
export CONSTRAINTLLM_SHARD_FILTER="${SHARDS}"
export CONSTRAINTLLM_REQUEST_TIMEOUT="${CONSTRAINTLLM_REQUEST_TIMEOUT:-600}"
export CONSTRAINTLLM_REQUEST_RETRIES="${CONSTRAINTLLM_REQUEST_RETRIES:-2}"
export CONSTRAINTLLM_REQUEST_RETRY_BACKOFF="${CONSTRAINTLLM_REQUEST_RETRY_BACKOFF:-5}"
export CONSTRAINTLLM_RETRIEVAL_CORPUS="${CONSTRAINTLLM_RETRIEVAL_CORPUS:-${ROOT_DIR}/data/knowledge_base.json}"

python -m constraintllm.run_csp --method "${METHOD}"
