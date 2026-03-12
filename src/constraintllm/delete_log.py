from __future__ import annotations

from pathlib import Path


def delete_log_xml_files(directory: str | Path) -> None:
    """Delete log and XML files from a temporary directory."""
    target = Path(directory)
    if not target.exists():
        return
    for pattern in ("*.log", "*.xml"):
        for file_path in target.rglob(pattern):
            try:
                file_path.unlink()
            except OSError:
                pass
