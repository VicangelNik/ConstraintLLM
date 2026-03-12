from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ProblemRecord:
    """A single IndusCP problem record."""

    name: str
    problem: str
    constraints: List[str] = field(default_factory=list)
    code: str = ""
    base_dir: Path | None = None
