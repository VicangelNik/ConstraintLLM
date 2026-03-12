from __future__ import annotations

import json
import re

from .config import CARM_TAG_CLASSIFICATION_SYSTEM_MESSAGE
from .llm import OpenAICompatibleLLM


def _parse_tag_response(raw_text: str) -> list[str]:
    """Parse model output into a tag list as robustly as possible."""
    if not raw_text:
        return []
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    bracket_match = re.search(r"\[(.*?)\]", raw_text, re.DOTALL)
    if not bracket_match:
        return []
    parts = [part.strip().strip('"\'') for part in bracket_match.group(1).split(",")]
    return [part for part in parts if part]


def classify_tag(problem_text: str, preset_constraints: list[str] | None = None, llm: OpenAICompatibleLLM | None = None) -> list[str]:
    """Prefer dataset tags when available, otherwise fall back to LLM classification."""
    if preset_constraints:
        return list(preset_constraints)
    if llm is None:
        return []
    raw_text = llm(CARM_TAG_CLASSIFICATION_SYSTEM_MESSAGE, problem_text, temperature=0.0)
    return _parse_tag_response(raw_text)
