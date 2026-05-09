"""Счётчик стабильных ID дыр H-NNN (минимум 3 знака, расширяется)."""
from __future__ import annotations
import re


_PAT = re.compile(r"^H-(\d+)$")


def max_id(ids: list[str]) -> int:
    nums = [int(m.group(1)) for m in (_PAT.match(x) for x in ids) if m]
    return max(nums) if nums else 0


def next_id(ids: list[str]) -> str:
    n = max_id(ids) + 1
    return f"H-{n:03d}" if n < 1000 else f"H-{n}"
