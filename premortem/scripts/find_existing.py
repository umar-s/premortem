"""Поиск существующего премортем-файла в docs/premortem/."""
from __future__ import annotations
from pathlib import Path
from scripts.slugify import slugify


class FindError(IOError):
    pass


def find_plan(root: Path, plan_name: str | None, return_all: bool = False) -> Path | list[Path] | None:
    """Возвращает путь к main md либо None."""
    if not root.exists():
        return [] if return_all else None
    candidates = sorted(p for p in root.iterdir()
                        if p.is_file() and p.suffix == ".md")
    if plan_name:
        slug = slugify(plan_name)
        for p in candidates:
            if p.stem == slug:
                return p
        return None
    if return_all:
        return candidates
    return candidates[0] if candidates else None
