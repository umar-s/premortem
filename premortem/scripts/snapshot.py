"""Создание снимка главного md в history/."""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path


def save_snapshot(main_path: Path, when: datetime | None = None) -> Path:
    when = when or datetime.now()
    history_dir = main_path.parent / "history"
    history_dir.mkdir(exist_ok=True)
    base = main_path.stem
    ts = when.strftime("%Y-%m-%d-%H%M")
    candidate = history_dir / f"{base}-{ts}.md"
    counter = 0
    while candidate.exists():
        counter += 1
        candidate = history_dir / f"{base}-{ts}_{counter}.md"
    shutil.copy2(main_path, candidate)
    return candidate
