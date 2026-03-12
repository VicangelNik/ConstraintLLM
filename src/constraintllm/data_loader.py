from __future__ import annotations

import json
from pathlib import Path

from .config import DATA_ROOT
from .dataset_classes import ProblemRecord


def load_induscp_records(statements_path: str | Path | None = None, max_items: int = 0) -> list[ProblemRecord]:
    """Load IndusCP problem statements and metadata."""
    target_path = Path(statements_path) if statements_path else DATA_ROOT / "statements.json"
    raw_items = json.loads(target_path.read_text(encoding="utf-8"))
    records: list[ProblemRecord] = []
    cost_data_root = DATA_ROOT / "cost_data"
    for item in raw_items:
        records.append(
            ProblemRecord(
                name=item["name"],
                problem=item.get("problem", ""),
                constraints=item.get("constraints", []),
                code=item.get("code", ""),
                base_dir=cost_data_root / item["name"],
            )
        )
    if max_items > 0:
        return records[:max_items]
    return records


def load_retrieval_corpus(corpus_path: str | Path) -> list[dict]:
    """Load the retrieval corpus."""
    target_path = Path(corpus_path)
    raw_items = json.loads(target_path.read_text(encoding="utf-8"))
    normalized = []
    for item in raw_items:
        normalized.append(
            {
                "name": item.get("name", "unknown"),
                "problem": item.get("problem", ""),
                "code": item.get("code", ""),
                "constraints": item.get("constraints", []),
            }
        )
    return normalized
