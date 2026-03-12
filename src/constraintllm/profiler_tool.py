from __future__ import annotations

import functools
import json
import time
from pathlib import Path


class SimpleProfiler:
    """Lightweight function timer."""

    def __init__(self) -> None:
        self.stats: dict[str, dict[str, float | int]] = {}

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                item = self.stats.setdefault(func.__name__, {"count": 0, "total": 0.0})
                item["count"] += 1
                item["total"] += duration
        return wrapper

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file_obj:
            json.dump(self.stats, file_obj, indent=2, ensure_ascii=False)


profiler = SimpleProfiler()
