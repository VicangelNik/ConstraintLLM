from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


def ensure_dir(path: Path) -> None:
    """Ensure that a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def extract_python_code(markdown_text: str | None) -> str | None:
    """Extract Python code from a Markdown code block."""
    if not markdown_text:
        return None
    match = re.search(r"```(?:python)?\s*(.*?)```", markdown_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if "from pycsp3 import *" in markdown_text:
        return markdown_text.strip()
    return None


def dump_json(data, output_path: Path) -> None:
    """Write data to a JSON file."""
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, indent=2, ensure_ascii=False)


def sanitize_name(name: str) -> str:
    """Replace special characters in a file name."""
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)


def collect_case_pairs(problem_dir: Path, max_cases: int) -> list[tuple[Path, Path | None]]:
    """Collect input/output file pairs for a problem."""
    pairs: list[tuple[Path, Path | None]] = []
    for input_path in sorted(problem_dir.glob("*.json"), key=lambda item: item.stem):
        output_path = problem_dir / f"{input_path.stem}.out"
        pairs.append((input_path, output_path if output_path.exists() else None))
    if max_cases > 0:
        return pairs[:max_cases]
    return pairs


def tokenize(text: str) -> set[str]:
    """Generate tokens for simple lexical retrieval."""
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]+", text.lower()))


def lexical_topk(query: str, documents: Iterable[dict], topk: int) -> list[dict]:
    """Perform simple retrieval using token overlap."""
    query_tokens = tokenize(query)
    scored: list[tuple[tuple[int, int], dict]] = []
    for document in documents:
        doc_tokens = tokenize(str(document.get("problem", "")))
        overlap = len(query_tokens & doc_tokens)
        scored.append(((-overlap, len(doc_tokens)), document))
    scored.sort(key=lambda item: item[0])
    return [item[1] for item in scored[:topk]]
