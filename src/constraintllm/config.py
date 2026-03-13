from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PACKAGE_ROOT / "data" / "induscp"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs"
TMP_ROOT = PACKAGE_ROOT / "tmp"


@dataclass(frozen=True)
class Settings:
    """Runtime settings."""

    api_base: str
    api_key: str
    model_name: str
    request_timeout: int
    request_retries: int
    request_retry_backoff: int
    time_limit: int
    topk: int
    revision_times: int
    cases_per_problem: int
    retrieval_corpus: str
    embedding_api_base: str
    embedding_api_key: str
    embedding_model: str
    embedding_batch_size: int
    prompt_problem_max_chars: int
    retrieval_example_problem_max_chars: int
    retrieval_example_code_max_chars: int
    retrieval_total_max_chars: int
    fix_problem_max_chars: int
    fix_code_max_chars: int
    fix_input_max_chars: int
    fix_output_max_chars: int
    fix_error_max_chars: int


def _get_int_env(name: str, default_value: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default_value
    try:
        return int(raw)
    except ValueError:
        return default_value


def get_settings() -> Settings:
    """Load settings from environment variables."""
    default_retrieval_corpus = str(PACKAGE_ROOT / "data" / "knowledge_base.json")
    return Settings(
        api_base=os.environ.get("CONSTRAINTLLM_API_BASE", "http://127.0.0.1:8000/v1").rstrip("/"),
        api_key=os.environ.get("CONSTRAINTLLM_API_KEY", "EMPTY"),
        model_name=os.environ.get("CONSTRAINTLLM_MODEL", "qwen2_5_32B"),
        request_timeout=_get_int_env("CONSTRAINTLLM_REQUEST_TIMEOUT", 600),
        request_retries=_get_int_env("CONSTRAINTLLM_REQUEST_RETRIES", 2),
        request_retry_backoff=_get_int_env("CONSTRAINTLLM_REQUEST_RETRY_BACKOFF", 5),
        time_limit=_get_int_env("CONSTRAINTLLM_TIME_LIMIT", 60),
        topk=_get_int_env("CONSTRAINTLLM_TOPK", 4),
        revision_times=_get_int_env("CONSTRAINTLLM_REVISION_TIMES", 2),
        cases_per_problem=_get_int_env("CONSTRAINTLLM_CASES_PER_PROBLEM", 5),
        retrieval_corpus=os.environ.get("CONSTRAINTLLM_RETRIEVAL_CORPUS", default_retrieval_corpus).strip(),
        embedding_api_base=os.environ.get("CONSTRAINTLLM_EMBEDDING_API_BASE", os.environ.get("CONSTRAINTLLM_API_BASE", "http://127.0.0.1:8000/v1")).rstrip("/"),
        embedding_api_key=os.environ.get("CONSTRAINTLLM_EMBEDDING_API_KEY", os.environ.get("CONSTRAINTLLM_API_KEY", "EMPTY")),
        embedding_model=os.environ.get("CONSTRAINTLLM_EMBEDDING_MODEL", "text-embedding-3-small").strip(),
        embedding_batch_size=_get_int_env("CONSTRAINTLLM_EMBEDDING_BATCH_SIZE", 32),
        prompt_problem_max_chars=_get_int_env("CONSTRAINTLLM_PROMPT_PROBLEM_MAX_CHARS", 12000),
        retrieval_example_problem_max_chars=_get_int_env("CONSTRAINTLLM_RETRIEVAL_EXAMPLE_PROBLEM_MAX_CHARS", 1800),
        retrieval_example_code_max_chars=_get_int_env("CONSTRAINTLLM_RETRIEVAL_EXAMPLE_CODE_MAX_CHARS", 2800),
        retrieval_total_max_chars=_get_int_env("CONSTRAINTLLM_RETRIEVAL_TOTAL_MAX_CHARS", 12000),
        fix_problem_max_chars=_get_int_env("CONSTRAINTLLM_FIX_PROBLEM_MAX_CHARS", 4000),
        fix_code_max_chars=_get_int_env("CONSTRAINTLLM_FIX_CODE_MAX_CHARS", 6000),
        fix_input_max_chars=_get_int_env("CONSTRAINTLLM_FIX_INPUT_MAX_CHARS", 2500),
        fix_output_max_chars=_get_int_env("CONSTRAINTLLM_FIX_OUTPUT_MAX_CHARS", 3000),
        fix_error_max_chars=_get_int_env("CONSTRAINTLLM_FIX_ERROR_MAX_CHARS", 2500),
    )


SYSTEM_MESSAGE_DIRECT = """You are an expert in constraint programming and PyCSP3.
Convert the given problem statement into correct PyCSP3 code.
Rules:
- Do not solve the problem manually.
- Only output Python code in a single ```python``` block.
- The code must read the instance from the built-in `data` variable.
- The code must be runnable with PyCSP3 using `python model.py -data=<file.json> -solve`.
- Prefer clear variable names and simple, verifiable constraints.
"""

COT_SYSTEM_MESSAGE = """You are an expert in constraint programming and PyCSP3.
Think carefully before coding, but only return the final Python code in a single ```python``` block.
Rules:
- Do not reveal hidden reasoning.
- Do not solve the instance manually.
- The code must read the instance from `data`.
- The code must be runnable with PyCSP3 using `python model.py -data=<file.json> -solve`.
"""

TOT_THOUGHT_SYSTEM_MESSAGE = """You are an expert in constraint programming and PyCSP3.
Produce a concise modelling plan for the problem.
Rules:
- Do not output Python code.
- Do not solve the instance manually.
- Focus on decision variables, domains, objective, and key constraints.
- Keep the plan short and concrete.
"""

FIX_CODE_SYSTEM_MESSAGE = """You are repairing a PyCSP3 model.
Return only corrected Python code inside one ```python``` block.
The repaired code must stay faithful to the original problem meaning.
"""

CARM_TAG_CLASSIFICATION_SYSTEM_MESSAGE = """Read the problem statement and infer a short list of likely constraint-programming tags.
Return only a JSON array of strings, such as [\"AllDifferent\", \"Sum\"].
"""
